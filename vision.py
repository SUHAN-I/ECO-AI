# ============================================================
# FILE: vision.py
# PURPOSE: Waste image classification using Llama 4 Scout Vision
# API: Groq (free, fast, accurate)
# MODEL: meta-llama/llama-4-scout-17b-16e-instruct
# USAGE: from vision import classify_waste, load_vision_client
# ============================================================
# INSTALL:
# pip install groq Pillow
# ============================================================

# ╔══════════════════════════════════════════════════════════╗
# ║                COLAB TESTING CELLS                       ║
# ║         Run cells in order: 1 → 2 → 3 → 4 → 5          ║
# ╚══════════════════════════════════════════════════════════╝

# ── COLAB CELL 1: Install ────────────────────────────────────
"""
!pip install groq Pillow -q
"""

# ── COLAB CELL 2: Load Client ────────────────────────────────
"""
exec(open('vision.py').read())

GROQ_API_KEY = "gsk_your_key_here"   # ← your Groq key

client = load_vision_client(GROQ_API_KEY)
print(f"✅ Vision client ready!")
"""

# ── COLAB CELL 3: Test With Waste Image ──────────────────────
"""
from google.colab import files
print("📸 Upload a waste image...")
uploaded = files.upload()
filename = list(uploaded.keys())[0]

result = test_vision(client, filename)
"""

# ── COLAB CELL 4: Test Multiple Images ───────────────────────
"""
from google.colab import files
print("📸 Upload multiple waste images...")
uploaded = files.upload()

for filename in uploaded.keys():
    print(f"\n{'='*52}")
    print(f"📸 Testing: {filename}")
    test_vision(client, filename)
"""

# ── COLAB CELL 5: Test Demo Fallback ─────────────────────────
"""
# Test that demo mode works (when API is unavailable)
result = mock_vision_response()
print(f"Demo result: {result['emoji']} {result['waste_type']}")
print(f"Demo Mode  : {result['is_demo']}")
"""


# ============================================================
#                 ACTUAL CODE STARTS HERE
# ============================================================

import io
import base64
import json
from PIL import Image


# ── CONFIGURATION ────────────────────────────────────────────
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_TOKENS   = 400
TEMPERATURE  = 0.1    # Low = consistent JSON output
IMAGE_SIZE   = 512    # Max image dimension (saves API bandwidth)
IMAGE_QUALITY= 85     # JPEG compression quality


# ── WASTE CATEGORY INFO ──────────────────────────────────────
# Used to enrich classification result with metadata
CATEGORY_INFO = {
    "plastic"  : {
        "label_en"     : "Plastic Waste",
        "emoji"        : "♻️",
        "recyclable"   : True,
        "market_search": "plastic PET HDPE LDPE scrap rate PKR recycling Pakistan",
        "color"        : "#2196F3"
    },
    "glass"    : {
        "label_en"     : "Glass Waste",
        "emoji"        : "♻️",
        "recyclable"   : True,
        "market_search": "glass bottle scrap rate PKR recycling Pakistan",
        "color"        : "#00BCD4"
    },
    "metal"    : {
        "label_en"     : "Metal / Scrap Waste",
        "emoji"        : "♻️",
        "recyclable"   : True,
        "market_search": "metal iron steel aluminium scrap rate PKR Misri Shah Pakistan",
        "color"        : "#9E9E9E"
    },
    "paper"    : {
        "label_en"     : "Paper Waste",
        "emoji"        : "♻️",
        "recyclable"   : True,
        "market_search": "paper newspaper scrap rate PKR Pakistan recycling",
        "color"        : "#FF9800"
    },
    "cardboard": {
        "label_en"     : "Cardboard Waste",
        "emoji"        : "♻️",
        "recyclable"   : True,
        "market_search": "cardboard box scrap rate PKR Pakistan recycling",
        "color"        : "#795548"
    },
    "e-waste"  : {
        "label_en"     : "Electronic Waste (E-Waste)",
        "emoji"        : "♻️",
        "recyclable"   : True,
        "market_search": "e-waste electronic circuit board scrap rate PKR Pakistan",
        "color"        : "#673AB7"
    },
    "textile"  : {
        "label_en"     : "Textile / Clothing Waste",
        "emoji"        : "♻️",
        "recyclable"   : True,
        "market_search": "textile cloth fabric scrap rate PKR recycling Pakistan",
        "color"        : "#E91E63"
    },
    "rubber"   : {
        "label_en"     : "Rubber Waste",
        "emoji"        : "♻️",
        "recyclable"   : True,
        "market_search": "rubber tyre scrap rate PKR pyrolysis Pakistan",
        "color"        : "#607D8B"
    },
    "organic"  : {
        "label_en"     : "Organic / Food Waste",
        "emoji"        : "🌱",
        "recyclable"   : False,
        "market_search": "organic waste composting biogas fertilizer Pakistan",
        "color"        : "#4CAF50"
    },
    "hazardous": {
        "label_en"     : "Hazardous Waste",
        "emoji"        : "☢️",
        "recyclable"   : False,
        "market_search": "hazardous waste disposal policy Pakistan Basel Convention",
        "color"        : "#F44336"
    },
    "trash"    : {
        "label_en"     : "General Non-Recyclable Trash",
        "emoji"        : "🗑️",
        "recyclable"   : False,
        "market_search": "waste disposal management Pakistan",
        "color"        : "#757575"
    },
    "unknown"  : {
        "label_en"     : "Unknown Waste",
        "emoji"        : "❓",
        "recyclable"   : False,
        "market_search": "waste recycling management Pakistan",
        "color"        : "#BDBDBD"
    },
}

# ── CLASSIFICATION PROMPT ─────────────────────────────────────
CLASSIFICATION_PROMPT = """You are a waste classification expert for Pakistan's circular economy app.
Your job is to identify waste/trash objects in images and classify them accurately.

Analyze the image carefully and respond ONLY with a valid JSON object.
No extra text, no markdown, no explanation outside the JSON.

Required JSON format:
{
  "waste_type": "specific name of the waste object visible in the image",
  "category": "one of: plastic / glass / metal / paper / cardboard / e-waste / textile / rubber / organic / hazardous / trash",
  "recyclable": true or false,
  "harmful_level": "one of: low / medium / high / very high",
  "urdu_label": "waste type written in Urdu script",
  "confidence": "one of: low / medium / high",
  "reasoning": "one clear sentence explaining your classification"
}

Classification guide:
- Plastic bottle / bag / wrapper / container / pipe  → plastic,   recyclable: true,  harmful: medium
- Glass bottle / jar / window glass                  → glass,     recyclable: true,  harmful: medium
- Metal can / tin / iron scrap / copper wire / steel → metal,     recyclable: true,  harmful: low
- Newspaper / book / office paper                    → paper,     recyclable: true,  harmful: low
- Cardboard box / packaging                          → cardboard, recyclable: true,  harmful: low
- Phone / laptop / TV / PCB / battery / charger      → e-waste,   recyclable: true,  harmful: very high
- Clothes / fabric / shoes / bags                    → textile,   recyclable: true,  harmful: low
- Tyre / rubber pipe / rubber mat                    → rubber,    recyclable: true,  harmful: medium
- Food scraps / fruit / vegetables / peels           → organic,   recyclable: false, harmful: low
- Medicine / syringe / chemical / pesticide          → hazardous, recyclable: false, harmful: very high
- Mixed unidentifiable waste                         → trash,     recyclable: false, harmful: medium

Urdu labels guide:
- plastic      → پلاسٹک فضلہ
- glass        → شیشے کا فضلہ
- metal can    → دھاتی ڈبہ
- aluminium can→ ایلومینیم ڈب
- paper        → کاغذ کا فضلہ
- cardboard    → گتے کا فضلہ
- e-waste      → الیکٹرانک فضلہ
- textile      → کپڑے کا فضلہ
- rubber/tyre  → ربڑ / ٹائر
- organic      → نامیاتی فضلہ
- hazardous    → خطرناک فضلہ
- trash        → کوڑا کرکٹ"""


# ════════════════════════════════════════════════════════════
# FUNCTION 1: Load Groq Client (once at startup)
# ════════════════════════════════════════════════════════════
def load_vision_client(groq_api_key):
    """
    Creates and returns a Groq API client.
    Call this ONCE at app startup.

    In Streamlit app.py:
        @st.cache_resource
        def get_vision_client():
            return load_vision_client(st.secrets["GROQ_API_KEY"])

    Args:
        groq_api_key : your Groq API key (starts with gsk_)

    Returns:
        Groq client object or None if failed
    """
    try:
        import groq
        client = groq.Groq(api_key=groq_api_key)

        # Quick connection test
        test = client.chat.completions.create(
            model      = VISION_MODEL,
            messages   = [{"role": "user", "content": "Hi"}],
            max_tokens = 5
        )
        print(f"✅ Groq Vision client loaded!")
        print(f"   Model: {VISION_MODEL}")
        return client

    except Exception as e:
        print(f"❌ Failed to load Groq client: {e}")
        print("   Check your GROQ_API_KEY and internet connection.")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 2: Convert Image to Base64
# ════════════════════════════════════════════════════════════
def image_to_base64(image_input):
    """
    Converts any image input to base64 JPEG string for API.

    Args:
        image_input : file path (str), PIL Image, bytes,
                      or Streamlit UploadedFile

    Returns:
        base64 encoded string
    """
    try:
        if isinstance(image_input, str):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        else:
            # Streamlit UploadedFile or file-like object
            img = Image.open(io.BytesIO(image_input.read())).convert("RGB")

        # Resize to save API bandwidth
        img.thumbnail((IMAGE_SIZE, IMAGE_SIZE))

        # Convert to JPEG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=IMAGE_QUALITY)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    except Exception as e:
        print(f"   ❌ Image conversion error: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 3: Mock Response (demo fallback)
# ════════════════════════════════════════════════════════════
def mock_vision_response():
    """
    Returns a demo result when API is unavailable.
    Keeps the app running during presentations / API downtime.
    """
    print("   🔄 Using DEMO response")
    cat = CATEGORY_INFO["plastic"]
    return {
        "waste_type"   : "Plastic Bottle",
        "label"        : "plastic",
        "label_en"     : cat["label_en"],
        "urdu_label"   : "پلاسٹک بوتل",
        "detected_obj" : "plastic bottle",
        "recyclable"   : True,
        "harmful_level": "medium",
        "confidence"   : "high",
        "reasoning"    : "Demo response — API not available",
        "emoji"        : cat["emoji"],
        "color"        : cat["color"],
        "market_search": cat["market_search"],
        "is_demo"      : True
    }


# ════════════════════════════════════════════════════════════
# FUNCTION 4: Main Classification
# ════════════════════════════════════════════════════════════
def classify_waste(client, image_input):
    """
    Classifies waste in an image using Llama 4 Scout Vision.

    The model sees the actual image and identifies:
    - Exact waste type (e.g. "aluminium can", "plastic bag")
    - Category (metal, plastic, organic etc.)
    - Recyclable or not
    - Harm level
    - Urdu label
    - Confidence level
    - Reasoning

    Args:
        client      : Groq client from load_vision_client()
        image_input : file path, PIL Image, bytes, or UploadedFile

    Returns:
        dict with complete waste classification result
    """
    print("\n🦙 Classifying waste with Llama 4 Scout Vision...")

    # Check client
    if client is None:
        print("   ❌ No Groq client — using demo.")
        return mock_vision_response()

    # Convert image to base64
    img_b64 = image_to_base64(image_input)
    if img_b64 is None:
        print("   ❌ Image conversion failed — using demo.")
        return mock_vision_response()

    print(f"   ✅ Image ready ({IMAGE_SIZE}px max)")

    try:
        # ── Call Groq API ─────────────────────────────────────
        response = client.chat.completions.create(
            model    = VISION_MODEL,
            messages = [
                {
                    "role"   : "user",
                    "content": [
                        {
                            "type": "text",
                            "text": CLASSIFICATION_PROMPT
                        },
                        {
                            "type"     : "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens  = MAX_TOKENS,
            temperature = TEMPERATURE
        )

        content = response.choices[0].message.content.strip()
        print(f"   📝 Raw response: {content}")

        # ── Clean & Parse JSON ────────────────────────────────
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)

        # ── Build Result ──────────────────────────────────────
        category   = data.get("category", "trash").lower().strip()
        recyclable = data.get("recyclable", False)

        # Get category metadata
        cat_info = CATEGORY_INFO.get(category, CATEGORY_INFO["unknown"])

        result = {
            "waste_type"   : data.get("waste_type", "Unknown Waste"),
            "label"        : category,
            "label_en"     : cat_info["label_en"],
            "urdu_label"   : data.get("urdu_label", "نامعلوم فضلہ"),
            "detected_obj" : data.get("waste_type", "unknown"),
            "recyclable"   : recyclable,
            "harmful_level": data.get("harmful_level", "medium"),
            "confidence"   : data.get("confidence", "medium"),
            "reasoning"    : data.get("reasoning", ""),
            "emoji"        : cat_info["emoji"],
            "color"        : cat_info["color"],
            "market_search": cat_info["market_search"],
            "is_demo"      : False
        }

        status = "Recyclable ♻️" if recyclable else "Non-Recyclable 🗑️"
        print(f"   ✅ {result['emoji']} {result['waste_type']} "
              f"→ {result['label_en']} ({status})")

        return result

    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parse error: {e}")
        print(f"   Raw content was: {content}")
        return mock_vision_response()

    except Exception as e:
        print(f"   ❌ API error: {e}")
        return mock_vision_response()


# ════════════════════════════════════════════════════════════
# FUNCTION 5: Test Helper (for Colab)
# ════════════════════════════════════════════════════════════
def test_vision(client, image_path):
    """
    Runs classification and prints a formatted result table.
    Use this in Colab testing cells.

    Args:
        client     : Groq client
        image_path : path to image file

    Returns:
        classification result dict
    """
    result = classify_waste(client, image_path)

    print("\n" + "=" * 55)
    print("  🦙 LLAMA 4 SCOUT VISION RESULT")
    print("=" * 55)
    print(f"  {result['emoji']}  Waste Type   : {result['waste_type']}")
    print(f"  📂  Category    : {result['label_en']}")
    print(f"  🇵🇰  اردو        : {result['urdu_label']}")
    print(f"  ♻️   Recyclable  : {'YES ✅' if result['recyclable'] else 'NO ❌'}")
    print(f"  ☣️   Harm Level  : {result['harmful_level'].upper()}")
    print(f"  📊  Confidence  : {result['confidence'].upper()}")
    print(f"  💬  Reasoning   : {result['reasoning']}")
    print(f"  🔎  RAG Query   : {result['market_search']}")
    print(f"  🔄  Demo Mode   : {'YES ⚠️' if result['is_demo'] else 'NO ✅'}")
    print("=" * 55)

    return result


# ════════════════════════════════════════════════════════════
# STREAMLIT USAGE (in app.py)
# ════════════════════════════════════════════════════════════
"""
import streamlit as st
from vision import load_vision_client, classify_waste

@st.cache_resource
def get_vision_client():
    return load_vision_client(st.secrets["GROQ_API_KEY"])

client = get_vision_client()

uploaded = st.camera_input("📸 Take photo of waste")
if uploaded:
    result = classify_waste(client, uploaded.getvalue())

    st.write(f"{result['emoji']} **{result['waste_type']}**")
    st.write(f"Category  : {result['label_en']}")
    st.write(f"اردو      : {result['urdu_label']}")
    st.write(f"Recyclable: {'YES ✅' if result['recyclable'] else 'NO ❌'}")
    st.write(f"Harm Level: {result['harmful_level']}")
"""


# ════════════════════════════════════════════════════════════
# STANDALONE TEST (python vision.py)
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import os

    print("=" * 55)
    print("  VISION MODULE — STANDALONE TEST")
    print("=" * 55)

    # Get API key from environment or prompt
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        api_key = input("Enter your Groq API key (gsk_...): ").strip()

    # Load client
    client = load_vision_client(api_key)

    if client:
        # Test with image if provided
        image_path = input("\nEnter image path to test (or press Enter to skip): ").strip()
        if image_path and os.path.exists(image_path):
            test_vision(client, image_path)
        else:
            print("\n✅ Client loaded successfully!")
            print("   Use test_vision(client, 'image.jpg') to test.")
            print("   Use classify_waste(client, image) in your app.")
