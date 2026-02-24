# ============================================================
# FILE: rag_engine.py
# PURPOSE: RAG pipeline — FAISS search + Llama 3.3-70B via Groq
# FLOW: Vision result → FAISS search → Llama → Urdu/English answer
# USAGE: from rag_engine import load_rag_components, run_rag_pipeline
# ============================================================
# INSTALL:
# pip install groq faiss-cpu sentence-transformers
# ============================================================

# ╔══════════════════════════════════════════════════════════╗
# ║                COLAB TESTING CELLS                       ║
# ║         Run cells in order: 1 → 2 → 3 → 4              ║
# ╚══════════════════════════════════════════════════════════╝

# ── COLAB CELL 1: Install ────────────────────────────────────
"""
!pip install groq faiss-cpu sentence-transformers -q
"""

# ── COLAB CELL 2: Load All Components ────────────────────────
"""
exec(open('rag_engine.py').read())

GROQ_API_KEY = "gsk_your_key_here"

# Load all components once
components = load_rag_components(GROQ_API_KEY)
print("✅ All RAG components ready!")
"""

# ── COLAB CELL 3: Test English ────────────────────────────────
"""
mock_vision = {
    "waste_type"   : "aluminium can",
    "label"        : "metal",
    "label_en"     : "Metal / Scrap Waste",
    "urdu_label"   : "ایلومینیم ڈب",
    "recyclable"   : True,
    "harmful_level": "low",
    "market_search": "metal iron steel aluminium scrap rate PKR Misri Shah Pakistan"
}

result = run_rag_pipeline(
    components    = components,
    vision_result = mock_vision,
    language      = "english"
)
print(f"\n📝 ENGLISH ANSWER:\n{result['answer']}")
"""

# ── COLAB CELL 4: Test Urdu ───────────────────────────────────
"""
result = run_rag_pipeline(
    components    = components,
    vision_result = mock_vision,
    language      = "urdu"
)
print(f"\n📝 URDU ANSWER:\n{result['answer']}")
"""

# ── COLAB CELL 5: Test With Custom Question ───────────────────
"""
result = run_rag_pipeline(
    components    = components,
    vision_result = mock_vision,
    user_question = "What is the startup cost for small scale recycling?",
    language      = "english"
)
print(f"\n📝 ANSWER:\n{result['answer']}")
"""


# ============================================================
#                 ACTUAL CODE STARTS HERE
# ============================================================

import os
import pickle
import numpy as np


# ── CONFIGURATION ────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
RAG_MODEL       = "llama-3.3-70b-versatile"   # Best Groq text model
FAISS_PATH      = "faiss_index/faiss.index"
CHUNKS_PATH     = "faiss_index/chunks.pkl"
TOP_K           = 4      # Number of FAISS chunks to retrieve
MAX_TOKENS      = 1500   # Max response length
TEMPERATURE     = 0.3    # Slightly creative but factual


# ── SYSTEM PROMPTS ────────────────────────────────────────────
URDU_SYSTEM_PROMPT = """آپ پاکستان کے ایک ماہر ویسٹ مینجمنٹ کنسلٹنٹ ہیں جو سرکلر اکانومی میں مہارت رکھتے ہیں۔
آپ کا کام لوگوں کو ان کے کچرے سے منافع بخش کاروبار شروع کرنے میں مدد کرنا ہے۔
ہمیشہ اردو میں جواب دیں اور پاکستانی مارکیٹ (مسری شاہ لاہور، کراچی سکریپ مارکیٹ) کا حوالہ دیں۔

جواب میں لازمی یہ 7 حصے شامل کریں:
1. 🗑️ فضلہ کی قسم اور تعارف
2. 💰 مارکیٹ ریٹ (PKR میں — نیچے دیے گئے ڈیٹا سے)
3. ♻️ ری سائیکلنگ کا مکمل طریقہ (مرحلہ وار)
4. 🏭 کاروبار کیسے شروع کریں (سرمایہ، اقدامات، مقام)
5. 🧪 صفائی کے کیمیکل اور حفاظتی اقدامات
6. ⚠️ نقصانات اور احتیاطی تدابیر
7. 💡 ماہانہ منافع کا اندازہ (PKR میں)"""

ENGLISH_SYSTEM_PROMPT = """You are an expert Waste Management Consultant for Pakistan's circular economy.
Your goal is to help people start profitable recycling businesses from waste.
Always reference Pakistani markets (Misri Shah Lahore, Karachi scrap markets).
Use the knowledge base data provided to give accurate PKR market rates.

Structure your response with exactly these 7 sections:
1. 🗑️ Waste Type Overview
2. 💰 Market Rate in Pakistan (PKR — use the data provided)
3. ♻️ Complete Recycling Process (step by step)
4. 🏭 Business Startup Guide (capital, steps, location)
5. 🧪 Cleaning Chemicals & Safety Measures
6. ⚠️ Hazards & Precautions
7. 💡 Estimated Monthly Profit (PKR)"""


# ════════════════════════════════════════════════════════════
# FUNCTION 1: Load All Components (once at startup)
# ════════════════════════════════════════════════════════════
def load_rag_components(groq_api_key):
    """
    Loads all RAG components at app startup.
    Call this ONCE — wrapped in @st.cache_resource in Streamlit.

    Loads:
    - FAISS index (vector search)
    - chunks.pkl (text + metadata)
    - SentenceTransformer (query embedding)
    - Groq client (LLM API)

    In Streamlit app.py:
        @st.cache_resource
        def get_rag_components():
            return load_rag_components(st.secrets["GROQ_API_KEY"])

    Args:
        groq_api_key : Groq API key (starts with gsk_)

    Returns:
        dict with all loaded components
    """
    import faiss
    import groq
    from sentence_transformers import SentenceTransformer

    print("⏳ Loading RAG components...")
    components = {}

    # Load FAISS index
    try:
        print("   Loading FAISS index...")
        components["index"]  = faiss.read_index(FAISS_PATH)
        with open(CHUNKS_PATH, "rb") as f:
            components["chunks"] = pickle.load(f)
        print(f"   ✅ FAISS: {components['index'].ntotal} vectors loaded")
    except Exception as e:
        print(f"   ❌ FAISS load failed: {e}")
        print(f"      Make sure faiss_index/ folder exists with both files")
        components["index"]  = None
        components["chunks"] = []

    # Load embedding model
    try:
        print("   Loading embedding model...")
        components["embedder"] = SentenceTransformer(EMBEDDING_MODEL)
        print(f"   ✅ Embedder: {EMBEDDING_MODEL}")
    except Exception as e:
        print(f"   ❌ Embedder load failed: {e}")
        components["embedder"] = None

    # Load Groq client
    try:
        print("   Loading Groq client...")
        client = groq.Groq(api_key=groq_api_key)
        # Quick test
        test = client.chat.completions.create(
            model      = RAG_MODEL,
            messages   = [{"role": "user", "content": "Hi"}],
            max_tokens = 5
        )
        components["client"] = client
        print(f"   ✅ Groq: {RAG_MODEL} ready")
    except Exception as e:
        print(f"   ❌ Groq load failed: {e}")
        components["client"] = None

    # Summary
    all_ok = all([
        components["index"]   is not None,
        components["embedder"]is not None,
        components["client"]  is not None,
    ])
    print(f"\n{'✅ All RAG components loaded!' if all_ok else '⚠️ Some components failed — demo mode active'}")
    return components


# ════════════════════════════════════════════════════════════
# FUNCTION 2: Search FAISS Index
# ════════════════════════════════════════════════════════════
def search_faiss(components, query, top_k=TOP_K):
    """
    Searches FAISS index for most relevant knowledge chunks.

    Converts query text to vector using the same embedding model
    used during ingestion, then finds most similar vectors.

    Args:
        components : loaded components dict
        query      : search query string (English or Urdu)
        top_k      : number of results to return

    Returns:
        list of chunk dicts with text, source, score
    """
    import faiss

    index    = components.get("index")
    chunks   = components.get("chunks", [])
    embedder = components.get("embedder")

    if index is None or embedder is None:
        print("   ⚠️ FAISS not available")
        return []

    print(f"\n🔍 Searching FAISS: '{query[:60]}...'")

    # Convert query to vector
    query_vec = embedder.encode([query]).astype("float32")
    faiss.normalize_L2(query_vec)

    # Search
    scores, indices = index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = chunks[idx]
        results.append({
            "text"  : chunk["text"],
            "source": chunk.get("source", "unknown"),
            "type"  : chunk.get("type", "unknown"),
            "score" : round(float(score), 3)
        })
        print(f"   📌 Score: {score:.3f} | "
              f"Source: {chunk.get('source'):20s} | "
              f"{chunk['text'][:70]}...")

    print(f"   ✅ Found {len(results)} relevant chunks!")
    return results


# ════════════════════════════════════════════════════════════
# FUNCTION 3: Build Context String
# ════════════════════════════════════════════════════════════
def build_context(chunks_found):
    """
    Builds a readable context string from FAISS search results.
    This context is injected into the Llama prompt as knowledge base.

    Higher scored chunks appear first for better relevance.

    Args:
        chunks_found : list of chunk dicts from search_faiss()

    Returns:
        formatted context string
    """
    if not chunks_found:
        return "No specific data found in knowledge base."

    context_parts = []
    for i, chunk in enumerate(chunks_found):
        context_parts.append(
            f"[Source {i+1} — {chunk['source']} | "
            f"Relevance Score: {chunk['score']}]\n"
            f"{chunk['text']}"
        )

    return "\n\n" + "\n\n".join(context_parts)


# ════════════════════════════════════════════════════════════
# FUNCTION 4: Build Prompts
# ════════════════════════════════════════════════════════════
def build_prompts(waste_label, waste_type, urdu_label,
                  recyclable, harmful_level, context,
                  language, user_question=""):
    """
    Builds system + user prompts for Llama.
    Uses language-specific prompts and injects FAISS context.

    Args:
        waste_label   : category (e.g. "metal")
        waste_type    : specific type (e.g. "aluminium can")
        urdu_label    : Urdu translation
        recyclable    : bool
        harmful_level : "low" / "medium" / "high" / "very high"
        context       : FAISS search results as text
        language      : "english" or "urdu"
        user_question : optional custom question from user

    Returns:
        (system_prompt, user_prompt) tuple
    """
    recyclable_text = "YES ♻️ (Recyclable)" if recyclable else "NO 🗑️ (Non-Recyclable)"

    if language == "urdu":
        system_prompt = URDU_SYSTEM_PROMPT
        user_prompt   = f"""فضلہ کی معلومات:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
• قسم        : {waste_type} ({urdu_label})
• کیٹیگری    : {waste_label}
• قابل ری سائیکل: {recyclable_text}
• نقصان دہ سطح : {harmful_level}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

علمی ڈیٹا بیس سے معلومات:
{context}

{"سوال: " + user_question if user_question else ""}

براہ کرم اس فضلے کے بارے میں مکمل کاروباری گائیڈ اردو میں دیں۔
مارکیٹ ریٹ PKR میں اور پاکستانی مارکیٹ کے مطابق بتائیں۔
جواب میں تمام 7 حصے شامل کریں۔"""

    else:  # english
        system_prompt = ENGLISH_SYSTEM_PROMPT
        user_prompt   = f"""Waste Information:
━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Type        : {waste_type}
• Category    : {waste_label}
• Urdu Label  : {urdu_label}
• Recyclable  : {recyclable_text}
• Harm Level  : {harmful_level}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Knowledge Base Data:
{context}

{"User Question: " + user_question if user_question else ""}

Provide a complete, detailed business startup guide for this waste type.
Include specific PKR market rates from the knowledge base above.
Reference Pakistani scrap markets (Misri Shah Lahore, Karachi).
Include all 7 sections in your response."""

    return system_prompt, user_prompt


# ════════════════════════════════════════════════════════════
# FUNCTION 5: Call Llama via Groq
# ════════════════════════════════════════════════════════════
def call_llama(components, system_prompt, user_prompt):
    """
    Sends prompt to Llama 3.3-70B via Groq API.
    Returns the generated text response.

    Args:
        components    : loaded components dict
        system_prompt : instructions for the model
        user_prompt   : user message with waste info + context

    Returns:
        response text string or None if failed
    """
    client = components.get("client")

    if client is None:
        print("   ⚠️ Groq client not available")
        return None

    print(f"\n🤖 Calling {RAG_MODEL} via Groq...")

    try:
        response = client.chat.completions.create(
            model    = RAG_MODEL,
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            max_tokens  = MAX_TOKENS,
            temperature = TEMPERATURE
        )

        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens
        print(f"   ✅ Response: {len(answer)} chars | Tokens used: {tokens}")
        return answer

    except Exception as e:
        print(f"   ❌ Llama API error: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 6: Mock Response (demo fallback)
# ════════════════════════════════════════════════════════════
def mock_rag_response(language, waste_type, urdu_label):
    """
    Returns a realistic demo response when API is unavailable.
    Keeps the app running during presentations / API downtime.
    """
    print("   🔄 Using DEMO RAG response")

    if language == "urdu":
        return f"""🗑️ **فضلہ کی قسم:** {waste_type} ({urdu_label})

💰 **مارکیٹ ریٹ:**
مسری شاہ مارکیٹ، لاہور میں اس فضلے کا ریٹ 85-140 روپے فی کلو ہے۔

♻️ **ری سائیکلنگ کا طریقہ:**
1. فضلہ اکٹھا کریں
2. صاف پانی سے دھوئیں
3. چھوٹے ٹکڑوں میں کاٹیں
4. قریبی ری سائیکلنگ سینٹر پر فروخت کریں

🏭 **کاروبار کیسے شروع کریں:**
• سرمایہ: 10,000 - 50,000 روپے
• مقام: مسری شاہ مارکیٹ یا قریبی سکریپ مارکیٹ
• اقدامات: جمع کریں → صاف کریں → فروخت کریں

🧪 **صفائی کیمیکل:** صابن اور پانی کافی ہے

⚠️ **احتیاط:** دستانے پہنیں، صاف جگہ پر کام کریں

💡 **ماہانہ منافع:** 15,000 - 45,000 روپے

⚠️ یہ ڈیمو جواب ہے — اصل جواب API سے آتا ہے"""

    else:
        return f"""🗑️ **Waste Type:** {waste_type}

💰 **Market Rate:** PKR 85-140/kg at Misri Shah Market, Lahore

♻️ **Recycling Process:**
1. Collect and sort waste
2. Clean with water and soap
3. Cut into smaller pieces
4. Sell to nearest recycling center

🏭 **Business Startup:**
• Capital : PKR 10,000 - 50,000
• Location: Misri Shah Market or nearby scrap market
• Steps   : Collect → Clean → Sell

🧪 **Cleaning Chemicals:** Soap and water sufficient

⚠️ **Safety:** Wear gloves, work in clean area

💡 **Monthly Profit:** PKR 15,000 - 45,000

⚠️ This is a DEMO response — real answer comes from API"""


# ════════════════════════════════════════════════════════════
# FUNCTION 7: Full RAG Pipeline (main entry point)
# ════════════════════════════════════════════════════════════
def run_rag_pipeline(components, vision_result,
                     user_question="", language="english"):
    """
    Runs the complete RAG pipeline end to end.

    Pipeline:
    1. Build search query from vision result
    2. Search FAISS for relevant knowledge chunks
    3. Build readable context from chunks
    4. Build language-specific prompt
    5. Call Llama 3.3-70B via Groq
    6. Return structured result

    Args:
        components    : dict from load_rag_components()
        vision_result : dict from vision.py classify_waste()
        user_question : optional follow-up question from user
        language      : "english" or "urdu"

    Returns:
        dict with:
            answer       : full text response from Llama
            language     : language used
            waste_type   : detected waste type
            waste_label  : waste category
            recyclable   : bool
            chunks_used  : number of FAISS chunks retrieved
            sources_used : list of data sources used
            is_demo      : True if using mock response
    """
    print("\n" + "=" * 58)
    print("  🚀 RAG PIPELINE STARTED")
    print("=" * 58)
    print(f"  Waste    : {vision_result.get('waste_type', 'Unknown')}")
    print(f"  Category : {vision_result.get('label_en', 'Unknown')}")
    print(f"  Language : {language.upper()}")
    if user_question:
        print(f"  Question : {user_question}")
    print("=" * 58)

    # ── Step 1: Build Smart Search Query ─────────────────────
    # Combine waste info + custom question for better search
    base_query   = vision_result.get("market_search", "")
    waste_type   = vision_result.get("waste_type", "waste")

    if user_question:
        search_query = f"{waste_type} {user_question} Pakistan PKR"
    else:
        search_query = base_query or f"{waste_type} scrap rate PKR Pakistan recycling"

    # ── Step 2: Search FAISS ──────────────────────────────────
    chunks_found = search_faiss(components, search_query)

    # ── Step 3: Build Context ─────────────────────────────────
    context = build_context(chunks_found)

    # ── Step 4: Build Prompts ─────────────────────────────────
    system_prompt, user_prompt = build_prompts(
        waste_label   = vision_result.get("label", "trash"),
        waste_type    = vision_result.get("waste_type", "Unknown"),
        urdu_label    = vision_result.get("urdu_label", "نامعلوم"),
        recyclable    = vision_result.get("recyclable", False),
        harmful_level = vision_result.get("harmful_level", "medium"),
        context       = context,
        language      = language,
        user_question = user_question
    )

    # ── Step 5: Call Llama ────────────────────────────────────
    answer  = call_llama(components, system_prompt, user_prompt)
    is_demo = False

    if not answer:
        answer  = mock_rag_response(
            language   = language,
            waste_type = vision_result.get("waste_type", "Unknown"),
            urdu_label = vision_result.get("urdu_label", "نامعلوم")
        )
        is_demo = True

    # ── Step 6: Build Result ──────────────────────────────────
    sources = list(set(c["source"] for c in chunks_found)) if chunks_found else []

    result = {
        "answer"      : answer,
        "language"    : language,
        "waste_type"  : vision_result.get("waste_type", "Unknown"),
        "waste_label" : vision_result.get("label", "trash"),
        "urdu_label"  : vision_result.get("urdu_label", "نامعلوم"),
        "recyclable"  : vision_result.get("recyclable", False),
        "chunks_used" : len(chunks_found),
        "sources_used": sources,
        "is_demo"     : is_demo
    }

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{'='*58}")
    print(f"  ✅ RAG PIPELINE COMPLETE")
    print(f"  Chunks used  : {len(chunks_found)}")
    print(f"  Sources      : {sources}")
    print(f"  Answer length: {len(answer)} chars")
    print(f"  Demo mode    : {is_demo}")
    print(f"{'='*58}")

    return result


# ════════════════════════════════════════════════════════════
# STREAMLIT USAGE (in app.py)
# ════════════════════════════════════════════════════════════
"""
import streamlit as st
from rag_engine import load_rag_components, run_rag_pipeline
from vision    import load_vision_client, classify_waste

# Load all components ONCE at startup
@st.cache_resource
def get_rag_components():
    return load_rag_components(st.secrets["GROQ_API_KEY"])

@st.cache_resource
def get_vision_client():
    from vision import load_vision_client
    return load_vision_client(st.secrets["GROQ_API_KEY"])

rag   = get_rag_components()
vclient = get_vision_client()

# In your UI:
uploaded = st.camera_input("📸 Take photo of waste")
language = st.radio("Language", ["english", "urdu"])

if uploaded:
    # Step 1: Vision classification
    vision_result = classify_waste(vclient, uploaded.getvalue())
    st.write(f"{vision_result['emoji']} {vision_result['waste_type']}")

    # Step 2: RAG pipeline
    rag_result = run_rag_pipeline(
        components    = rag,
        vision_result = vision_result,
        language      = language
    )
    st.markdown(rag_result['answer'])
"""


# ════════════════════════════════════════════════════════════
# STANDALONE TEST (python rag_engine.py)
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 58)
    print("  RAG ENGINE — STANDALONE TEST")
    print("=" * 58)

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        api_key = input("Enter Groq API key (gsk_...): ").strip()

    # Load components
    components = load_rag_components(api_key)

    # Mock vision result for testing
    mock_vision = {
        "waste_type"   : "aluminium can",
        "label"        : "metal",
        "label_en"     : "Metal / Scrap Waste",
        "urdu_label"   : "ایلومینیم ڈب",
        "recyclable"   : True,
        "harmful_level": "low",
        "market_search": "metal iron steel aluminium scrap rate PKR Misri Shah Pakistan"
    }

    # Test English
    print("\n🧪 TEST 1 — ENGLISH")
    result_en = run_rag_pipeline(components, mock_vision, language="english")
    print(f"\n📝 ANSWER:\n{result_en['answer'][:500]}...")

    # Test Urdu
    print("\n🧪 TEST 2 — URDU")
    result_ur = run_rag_pipeline(components, mock_vision, language="urdu")
    print(f"\n📝 ANSWER:\n{result_ur['answer'][:500]}...")

    print("\n✅ RAG Engine test complete!")
