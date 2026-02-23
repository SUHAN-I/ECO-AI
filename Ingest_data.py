# ============================================================
# FILE: ingest_data.py
# PURPOSE: Load PDF and CSV data into Qdrant Vector Database
# RUN: Only once — to populate Qdrant with your knowledge base
# AUTHOR: Waste Management GenAI App
# ============================================================

# ── IMPORTS ─────────────────────────────────────────────────
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import pypdf
import pandas as pd
import uuid
import os

# ── CONFIGURATION ────────────────────────────────────────────
# Qdrant Cloud credentials
QDRANT_URL     = "https://249b7e90-db7c-4faa-a652-782b14ef64a0.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.xDhxC-eywGm1NahB6JiSCuK9EWSBqPEUrq3JlrKTa-o"

# Collection and model settings
COLLECTION_NAME = "waste_knowledge"
VECTOR_SIZE     = 384        # Must match the embedding model output
CHUNK_SIZE      = 500        # Characters per text chunk
CHUNK_OVERLAP   = 50         # Overlapping characters between chunks
BATCH_SIZE      = 50         # Number of vectors to upload at once

# Your data files — update paths when running locally or on Streamlit
PDF_FOLDERS = [
    {"path": "data/pdfs", "label": "recycling_knowledge"},  # Folder with your PDFs
]
CSV_FILE_PATH = "data/Scrap_Price.csv"                      # Your CSV file


# ── CONNECT TO QDRANT ────────────────────────────────────────
def get_qdrant_client():
    """Creates and returns a Qdrant client connection."""
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print("✅ Connected to Qdrant Cloud")
    return client


# ── LOAD EMBEDDING MODEL ─────────────────────────────────────
def get_embedding_model():
    """
    Loads the multilingual embedding model.
    Supports Urdu, English, and 50+ languages.
    """
    print("⏳ Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    print(f"✅ Embedding model loaded! Vector size: {VECTOR_SIZE}")
    return model


# ── CREATE QDRANT COLLECTION ─────────────────────────────────
def create_collection(client):
    """
    Creates the Qdrant collection if it does not already exist.
    A collection is like a table — it stores all your vectors.
    """
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing:
        print(f"⚠️  Collection '{COLLECTION_NAME}' already exists — skipping creation.")
    else:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE  # Best distance metric for text similarity
            )
        )
        print(f"✅ Collection '{COLLECTION_NAME}' created successfully!")


# ── TEXT CHUNKER ─────────────────────────────────────────────
def split_text_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Splits long text into smaller overlapping chunks.
    Overlap ensures answers are not cut off at chunk boundaries.
    """
    chunks = []
    start  = 0

    while start < len(text):
        end   = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) > 30:          # Skip very short/empty chunks
            chunks.append(chunk)
        start = end - overlap

    return chunks


# ── PDF UPLOADER ─────────────────────────────────────────────
def upload_pdf_to_qdrant(client, model, pdf_path, source_label="recycling_knowledge"):
    """
    Reads a PDF file, splits into chunks, converts to vectors,
    and uploads everything to Qdrant with metadata.
    """
    print(f"\n📄 Reading PDF: {os.path.basename(pdf_path)}")

    if not os.path.exists(pdf_path):
        print(f"   ❌ File not found: {pdf_path}")
        return 0

    # Extract text from all pages
    reader      = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"   Found {total_pages} pages.")

    all_chunks = []

    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()

        if not page_text or len(page_text.strip()) < 20:
            print(f"   ⚠️  Page {page_num + 1} is empty — skipping.")
            continue

        for chunk in split_text_into_chunks(page_text):
            all_chunks.append({
                "text"  : chunk,
                "source": source_label,
                "page"  : page_num + 1,
                "file"  : os.path.basename(pdf_path)
            })

    print(f"   Total chunks created: {len(all_chunks)}")

    # Convert chunks to vectors and upload in batches
    points = []
    for i, chunk_data in enumerate(all_chunks):
        vector = model.encode(chunk_data["text"]).tolist()
        points.append(PointStruct(
            id      = str(uuid.uuid4()),
            vector  = vector,
            payload = {
                "text"  : chunk_data["text"],
                "source": chunk_data["source"],
                "page"  : chunk_data["page"],
                "file"  : chunk_data["file"],
                "type"  : "pdf"
            }
        ))

        if len(points) >= BATCH_SIZE:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f"   ✅ Uploaded batch... ({i + 1}/{len(all_chunks)} chunks done)")
            points = []

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"   ✅ Uploaded final batch of {len(points)} chunks.")

    print(f"🎉 PDF done! {len(all_chunks)} chunks stored.")
    return len(all_chunks)


# ── CSV UPLOADER ─────────────────────────────────────────────
def upload_csv_to_qdrant(client, model, csv_path, source_label="market_rates"):
    """
    Reads a CSV file, converts each row to a readable text string,
    and uploads to Qdrant with full row metadata.

    Expected CSV columns: Category, Material, Price, Unit, Date_Scraped
    """
    print(f"\n📊 Reading CSV: {os.path.basename(csv_path)}")

    if not os.path.exists(csv_path):
        print(f"   ❌ File not found: {csv_path}")
        return 0

    df = pd.read_csv(csv_path)
    print(f"   Found {len(df)} rows and {len(df.columns)} columns.")
    print(f"   Columns: {list(df.columns)}")

    points = []

    for i, row in df.iterrows():
        # Convert row to readable sentence
        # Example: "Category: Plastic | Material: Bottle | Price: RS 85/kg"
        row_text = " | ".join([
            f"{col}: {str(val)}"
            for col, val in row.items()
            if pd.notna(val)
        ])

        if len(row_text.strip()) < 10:
            continue

        vector = model.encode(row_text).tolist()
        points.append(PointStruct(
            id      = str(uuid.uuid4()),
            vector  = vector,
            payload = {
                "text"     : row_text,
                "source"   : source_label,
                "row_index": i,
                "file"     : os.path.basename(csv_path),
                "type"     : "csv",
                # Store each column as its own field for easy filtering
                **{str(col): str(val) for col, val in row.items() if pd.notna(val)}
            }
        ))

        if len(points) >= BATCH_SIZE:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            print(f"   ✅ Uploaded batch... ({i + 1}/{len(df)} rows done)")
            points = []

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        print(f"   ✅ Uploaded final batch of {len(points)} rows.")

    print(f"🎉 CSV done! {len(df)} rows stored.")
    return len(df)


# ── SEARCH TESTER ────────────────────────────────────────────
def test_search(client, model, query_text, top_k=3):
    """
    Tests that Qdrant can find relevant results for a query.
    Supports both English and Urdu queries.
    """
    print(f"\n🔍 Searching: '{query_text}'")
    print("-" * 50)

    query_vector = model.encode(query_text).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    ).points

    if not results:
        print("❌ No results found.")
        return

    for i, result in enumerate(results):
        print(f"\n📌 Result {i + 1} (Score: {result.score:.3f})")
        print(f"   Source : {result.payload.get('source', 'unknown')}")
        print(f"   Type   : {result.payload.get('type', 'unknown')}")
        print(f"   Preview: {result.payload.get('text', '')[:200]}...")

    print("\n✅ Search test complete!")


# ── MAIN ─────────────────────────────────────────────────────
def main():
    """
    Main function — runs the full ingestion pipeline.
    1. Connect to Qdrant
    2. Load embedding model
    3. Create collection
    4. Upload all PDFs
    5. Upload CSV
    6. Run search tests
    """
    print("=" * 55)
    print("  WASTE MANAGEMENT APP — DATA INGESTION PIPELINE")
    print("=" * 55)

    # Setup
    client = get_qdrant_client()
    model  = get_embedding_model()
    create_collection(client)

    total_chunks = 0

    # Upload PDFs from all folders
    for folder_info in PDF_FOLDERS:
        folder_path = folder_info["path"]
        label       = folder_info["label"]

        if not os.path.exists(folder_path):
            print(f"\n❌ PDF folder not found: {folder_path}")
            continue

        pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
        print(f"\n📁 Folder: {folder_path} — Found {len(pdf_files)} PDFs")

        for pdf_file in pdf_files:
            full_path     = os.path.join(folder_path, pdf_file)
            total_chunks += upload_pdf_to_qdrant(client, model, full_path, label)

    # Upload CSV
    total_chunks += upload_csv_to_qdrant(client, model, CSV_FILE_PATH, "market_rates")

    # Final stats
    info = client.get_collection(COLLECTION_NAME)
    print("\n" + "=" * 55)
    print(f"  ✅ INGESTION COMPLETE!")
    print(f"  Total vectors in Qdrant : {info.points_count}")
    print(f"  Collection              : {COLLECTION_NAME}")
    print("=" * 55)

    # Search tests
    print("\n🧪 Running search tests...")
    test_search(client, model, "plastic scrap rate Pakistan")
    test_search(client, model, "recycling waste business startup")
    test_search(client, model, "پلاسٹک کاروبار")


if __name__ == "__main__":
    main()
