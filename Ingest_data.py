# ============================================================
# FILE: ingest_data.py
# PURPOSE: Extract text from ALL data files → Build FAISS index
# RUN: Only ONCE (on your PC or Colab) to build the index
# OUTPUT: faiss_index/faiss.index + faiss_index/chunks.pkl
# THEN: Push faiss_index/ folder to GitHub
# ============================================================
# INSTALL:
# pip install faiss-cpu sentence-transformers pypdf pandas openpyxl
# ============================================================

import os
import pickle
import numpy as np
import faiss
import pypdf
import pandas as pd
from sentence_transformers import SentenceTransformer

# ── CONFIGURATION ────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_SIZE     = 384    # Must match embedding model output
CHUNK_SIZE      = 500    # Characters per text chunk
CHUNK_OVERLAP   = 50     # Overlap between chunks (prevents cut-off answers)

# Output paths — these files go to GitHub
FAISS_DIR   = "faiss_index"
FAISS_PATH  = os.path.join(FAISS_DIR, "faiss.index")
CHUNKS_PATH = os.path.join(FAISS_DIR, "chunks.pkl")

# ── DATA FILE PATHS ──────────────────────────────────────────
# Update these paths to match your actual file locations
# GitHub repo structure:
#   data/
#     pdfs/    ← all PDF files here
#     xlsx/    ← all XLSX files here
#     csv/     ← all CSV files here

PDF_FILES = [
    {
        "path" : "data/pdfs/RECYCLING_KNOWLEDGE.pdf",
        "label": "recycling_knowledge"
    },
    {
        "path" : "data/pdfs/Recycling_Knowledge_Dataset_PKR.pdf",
        "label": "recycling_knowledge"
    },
    {
        "path" : "data/pdfs/World_Bank_Plastic_Waste_Pakistan.pdf",
        "label": "plastic_waste_research"
    },
    {
        "path" : "data/pdfs/National_Hazardous_Waste_Policy_2022.pdf",
        "label": "waste_policy"
    },
]

XLSX_FILES = [
    {
        "path" : "data/xlsx/RECYCLING_KNOWLEDGE.xlsx",
        "label": "recycling_knowledge"
    },
]

CSV_FILES = [
    {
        "path" : "data/csv/Scrap_Price.csv",
        "label": "market_rates"
    },
    # Add more CSV files here if needed:
    # {"path": "data/csv/market_rates_city2.csv", "label": "market_rates"},
]


# ════════════════════════════════════════════════════════════
# STEP 1 — LOAD EMBEDDING MODEL
# ════════════════════════════════════════════════════════════
def load_embedding_model():
    """
    Loads the multilingual sentence transformer model.
    - Supports Urdu, English, and 50+ languages
    - Vector size: 384
    - Model size: ~470MB (downloaded once, cached)
    """
    print("⏳ Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"✅ Embedding model loaded! Vector size: {VECTOR_SIZE}")
    return model


# ════════════════════════════════════════════════════════════
# STEP 2 — TEXT CHUNKER (shared by all extractors)
# ════════════════════════════════════════════════════════════
def split_into_chunks(text, source_label, file_name, extra_meta=None):
    """
    Splits long text into smaller overlapping chunks.

    Why overlap? If an answer sits at the boundary between
    two chunks, overlap ensures it is not cut off.

    Args:
        text         : raw text to split
        source_label : tag for this data source (e.g. 'market_rates')
        file_name    : original filename for reference
        extra_meta   : any additional metadata dict to attach

    Returns:
        list of chunk dicts: {text, source, file, ...}
    """
    chunks = []
    start  = 0
    text   = text.strip()

    while start < len(text):
        end   = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if len(chunk) > 30:  # Skip very short/empty chunks
            chunk_data = {
                "text"  : chunk,
                "source": source_label,
                "file"  : file_name,
            }
            if extra_meta:
                chunk_data.update(extra_meta)
            chunks.append(chunk_data)

        start = end - CHUNK_OVERLAP

    return chunks


# ════════════════════════════════════════════════════════════
# STEP 3a — PDF EXTRACTOR
# ════════════════════════════════════════════════════════════
def extract_from_pdf(pdf_path, source_label):
    """
    Reads a PDF file page by page.
    Extracts text from each page and splits into chunks.
    Skips blank or unreadable pages automatically.

    Returns: list of chunk dicts
    """
    file_name = os.path.basename(pdf_path)
    print(f"\n  📄 PDF: {file_name}")

    if not os.path.exists(pdf_path):
        print(f"     ❌ File not found — skipping.")
        return []

    reader     = pypdf.PdfReader(pdf_path)
    all_chunks = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()

        # Skip empty pages
        if not text or len(text.strip()) < 20:
            continue

        page_chunks = split_into_chunks(
            text        = text,
            source_label= source_label,
            file_name   = file_name,
            extra_meta  = {"page": page_num + 1, "type": "pdf"}
        )
        all_chunks.extend(page_chunks)

    print(f"     ✅ {len(all_chunks)} chunks from {len(reader.pages)} pages")
    return all_chunks


# ════════════════════════════════════════════════════════════
# STEP 3b — XLSX EXTRACTOR
# ════════════════════════════════════════════════════════════
def extract_from_xlsx(xlsx_path, source_label):
    """
    Reads all sheets in an Excel file.
    Each row is converted to a readable text string.

    Example row output:
    "Material: PET Plastic | Process: Melting | Price: 84-168 PKR/kg"

    Returns: list of chunk dicts
    """
    file_name = os.path.basename(xlsx_path)
    print(f"\n  📊 XLSX: {file_name}")

    if not os.path.exists(xlsx_path):
        print(f"     ❌ File not found — skipping.")
        return []

    chunks = []

    try:
        xl     = pd.ExcelFile(xlsx_path)
        sheets = xl.sheet_names
        print(f"     Sheets found: {sheets}")

        for sheet in sheets:
            df = pd.read_excel(xlsx_path, sheet_name=sheet)

            for i, row in df.iterrows():
                # Convert all columns to readable key:value pairs
                row_text = " | ".join([
                    f"{col}: {str(val)}"
                    for col, val in row.items()
                    if pd.notna(val) and str(val).strip() != ""
                ])

                if len(row_text.strip()) < 10:
                    continue

                chunks.append({
                    "text"  : row_text,
                    "source": source_label,
                    "file"  : file_name,
                    "sheet" : sheet,
                    "row"   : i,
                    "type"  : "xlsx"
                })

        print(f"     ✅ {len(chunks)} chunks from XLSX")

    except Exception as e:
        print(f"     ❌ Error reading XLSX: {e}")

    return chunks


# ════════════════════════════════════════════════════════════
# STEP 3c — CSV EXTRACTOR
# ════════════════════════════════════════════════════════════
def extract_from_csv(csv_path, source_label):
    """
    Reads a CSV file.
    Each row is converted to a readable text string.

    Expected columns (flexible — works with any columns):
    Category | Material | Price | Unit | Date_Scraped

    Example row output:
    "Category: Plastic | Material: Bottle | Price: RS 85/kg"

    Returns: list of chunk dicts
    """
    file_name = os.path.basename(csv_path)
    print(f"\n  📋 CSV: {file_name}")

    if not os.path.exists(csv_path):
        print(f"     ❌ File not found — skipping.")
        return []

    chunks = []

    try:
        df = pd.read_csv(csv_path)
        print(f"     {len(df)} rows × {len(df.columns)} columns")
        print(f"     Columns: {list(df.columns)}")

        for i, row in df.iterrows():
            row_text = " | ".join([
                f"{col}: {str(val)}"
                for col, val in row.items()
                if pd.notna(val) and str(val).strip() != ""
            ])

            if len(row_text.strip()) < 10:
                continue

            chunks.append({
                "text"  : row_text,
                "source": source_label,
                "file"  : file_name,
                "row"   : i,
                "type"  : "csv",
                # Store each column as individual field for filtering
                **{str(col): str(val) for col, val in row.items() if pd.notna(val)}
            })

        print(f"     ✅ {len(chunks)} chunks from CSV")

    except Exception as e:
        print(f"     ❌ Error reading CSV: {e}")

    return chunks


# ════════════════════════════════════════════════════════════
# STEP 4 — BUILD FAISS INDEX
# ════════════════════════════════════════════════════════════
def build_faiss_index(all_chunks, model):
    """
    Converts all text chunks to vectors and builds FAISS index.

    FAISS = Facebook AI Similarity Search
    - Completely free, runs locally
    - No internet needed after building
    - Finds most similar text in milliseconds
    - Only 1.12 MB for 762 vectors!

    Process:
    1. Extract text from all chunks
    2. Convert to 384-dimensional vectors
    3. Normalize (for cosine similarity)
    4. Add to FAISS IndexFlatIP

    Returns: (faiss_index, chunks_list)
    """
    print(f"\n⏳ Building FAISS index for {len(all_chunks)} chunks...")

    texts = [chunk["text"] for chunk in all_chunks]

    print("   Converting text to vectors (batch processing)...")
    vectors = model.encode(
        texts,
        batch_size        = 32,   # Process 32 at a time → saves RAM
        show_progress_bar = True
    )

    # Convert to float32 (FAISS requirement)
    vectors = np.array(vectors).astype("float32")

    # Normalize vectors for cosine similarity
    faiss.normalize_L2(vectors)

    # Create and populate the index
    # IndexFlatIP = exact search using inner product (cosine after normalization)
    index = faiss.IndexFlatIP(VECTOR_SIZE)
    index.add(vectors)

    print(f"   ✅ FAISS index built! Total vectors: {index.ntotal}")
    return index, all_chunks


# ════════════════════════════════════════════════════════════
# STEP 5 — SAVE TO DISK
# ════════════════════════════════════════════════════════════
def save_faiss_index(index, chunks):
    """
    Saves two files to the faiss_index/ folder:

    faiss.index → the searchable vector database
                  (loaded by app at startup for fast search)

    chunks.pkl  → the original text + metadata for each vector
                  (used to retrieve actual text after searching)

    Both files are pushed to GitHub.
    The app loads them ONCE at startup — no rebuilding ever needed!
    """
    os.makedirs(FAISS_DIR, exist_ok=True)

    # Save FAISS index
    faiss.write_index(index, FAISS_PATH)
    print(f"   ✅ Saved → {FAISS_PATH}")

    # Save chunks using pickle
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)
    print(f"   ✅ Saved → {CHUNKS_PATH}")

    # Show file sizes
    index_mb  = os.path.getsize(FAISS_PATH)  / (1024 * 1024)
    chunks_mb = os.path.getsize(CHUNKS_PATH) / (1024 * 1024)
    print(f"   📦 faiss.index size : {index_mb:.2f} MB")
    print(f"   📦 chunks.pkl size  : {chunks_mb:.2f} MB")
    print(f"   📦 Total size       : {index_mb + chunks_mb:.2f} MB")


# ════════════════════════════════════════════════════════════
# STEP 6 — TEST SEARCH
# ════════════════════════════════════════════════════════════
def test_search(index, chunks, model, query, top_k=3):
    """
    Verifies the FAISS index is working correctly.
    Tests both English and Urdu queries.
    """
    print(f"\n🔍 Test: '{query}'")
    print("-" * 55)

    # Convert query to vector
    query_vec = model.encode([query]).astype("float32")
    faiss.normalize_L2(query_vec)

    # Search FAISS
    scores, indices = index.search(query_vec, top_k)

    for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
        if idx == -1:
            continue
        chunk = chunks[idx]
        print(f"  📌 #{rank+1} Score: {score:.3f} | "
              f"Source: {chunk.get('source')} | "
              f"Type: {chunk.get('type')}")
        print(f"     {chunk['text'][:180]}...")

    print("  ✅ Done!")


# ════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════════
def main():
    """
    Runs the full ingestion pipeline:
    1. Load embedding model
    2. Extract text from PDFs, XLSX, CSV files
    3. Build FAISS index
    4. Save to disk
    5. Run search tests to verify
    """
    print("=" * 60)
    print("  WASTE MANAGEMENT APP — FAISS INDEX BUILDER")
    print("=" * 60)

    # Step 1: Load model
    model      = load_embedding_model()
    all_chunks = []

    # Step 2a: Extract from all PDFs
    print("\n📂 Processing PDF files...")
    for f in PDF_FILES:
        chunks = extract_from_pdf(f["path"], f["label"])
        all_chunks.extend(chunks)

    # Step 2b: Extract from all XLSX files
    print("\n📂 Processing XLSX files...")
    for f in XLSX_FILES:
        chunks = extract_from_xlsx(f["path"], f["label"])
        all_chunks.extend(chunks)

    # Step 2c: Extract from all CSV files
    print("\n📂 Processing CSV files...")
    for f in CSV_FILES:
        chunks = extract_from_csv(f["path"], f["label"])
        all_chunks.extend(chunks)

    # Summary by source
    print(f"\n📊 Total chunks extracted: {len(all_chunks)}")
    by_source = {}
    for c in all_chunks:
        src = c.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
    for src, count in by_source.items():
        print(f"   {src:30s}: {count} chunks")

    if len(all_chunks) == 0:
        print("\n❌ No chunks found! Update the file paths above.")
        return

    # Step 3: Build FAISS index
    index, chunks = build_faiss_index(all_chunks, model)

    # Step 4: Save to disk
    print("\n💾 Saving FAISS index to disk...")
    save_faiss_index(index, chunks)

    # Step 5: Run test searches
    print("\n🧪 Running search verification tests...")
    test_search(index, chunks, model, "plastic bottle recycling rate PKR")
    test_search(index, chunks, model, "scrap price market Lahore Pakistan")
    test_search(index, chunks, model, "پلاسٹک ری سائیکلنگ کاروبار")
    test_search(index, chunks, model, "hazardous waste policy Pakistan law")
    test_search(index, chunks, model, "startup business waste recycling steps")

    # Final summary
    print("\n" + "=" * 60)
    print("  ✅ FAISS INDEX COMPLETE!")
    print(f"  Total vectors stored : {index.ntotal}")
    print(f"  Index saved to       : {FAISS_DIR}/")
    print("\n  NEXT STEPS:")
    print("  1. Download faiss_index/faiss.index")
    print("  2. Download faiss_index/chunks.pkl")
    print("  3. Push both files to GitHub in faiss_index/ folder")
    print("  4. App loads them automatically at startup ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
