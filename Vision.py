# ============================================================
# FILE: vision.py
# PURPOSE: Waste image classification using Roboflow API
# MODEL: YOLO11 (fine-tuned on waste dataset)
# NOTE: Fill in your Roboflow API details when ready
# ============================================================
ROBOFLOW_API_KEY   = "your_roboflow_api_key_here"  # ← your key
ROBOFLOW_WORKSPACE = "your_workspace_name"          # ← from URL
ROBOFLOW_PROJECT   = "waste-classifier"             # ← project name
ROBOFLOW_VERSION   = "1"                            # ← version number


# ── IMPORTS ─────────────────────────────────────────────────
import requests
import base64
import json
from PIL import Image
import io
import os

# ── CONFIGURATION ────────────────────────────────────────────
# TODO: Fill these in after setting up Roboflow
ROBOFLOW_API_KEY   = "your_roboflow_api_key_here"   # ← paste your Roboflow API key
ROBOFLOW_WORKSPACE = "your_workspace_name"           # ← your Roboflow workspace
ROBOFLOW_PROJECT   = "waste-classifier"              # ← your Roboflow project name
ROBOFLOW_VERSION   = "1"                             # ← your model version number

# Roboflow API URL (do not change this)
ROBOFLOW_API_URL = (
    f"https://classify.roboflow.com/"
    f"{ROBOFLOW_PROJECT}/{ROBOFLOW_VERSION}"
    f"?api_key={ROBOFLOW_API_KEY}"
)

# Waste keywords for recyclable detection
RECYCLABLE_KEYWORDS = [
    "plastic", "paper", "cardboard", "glass",
    "metal", "iron", "copper", "aluminium", "aluminum",
    "recyclable", "bottle", "can", "tin", "scrap"
]
NON_RECYCLABLE_KEYWORDS = [
    "non-recyclable", "non recyclable", "organic",
    "food waste", "medical", "hazardous", "styrofoam"
]


# ── IMAGE PREPARATION ────────────────────────────────────────
def prepare_image(image_input, max_size=(640, 640)):
    """
    Accepts either a file path (str) or a PIL Image object.
    Resizes and converts to base64 string for Roboflow API.

    Returns:
        img_base64 (str) : base64 encoded image string
        img_size   (tuple): (width, height) of resized image
    """
    # Handle both file path and PIL Image input
    if isinstance(image_input, str):
        img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        # Handle raw bytes (from Streamlit file uploader)
        img = Image.open(io.BytesIO(image_input)).convert("RGB")

    # Resize while keeping aspect ratio
    img.thumbnail(max_size)

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    img_bytes   = buffer.getvalue()
    img_base64  = base64.b64encode(img_bytes).decode("utf-8")

    return img_base64, img.size


# ── RECYCLABLE CHECKER ───────────────────────────────────────
def is_recyclable(label):
    """
    Checks if a waste label is recyclable based on keywords.

    Args:
        label (str): The waste label from YOLO model

    Returns:
        bool: True if recyclable, False if not
    """
    label_lower = label.lower()

    for word in NON_RECYCLABLE_KEYWORDS:
        if word in label_lower:
            return False

    for word in RECYCLABLE_KEYWORDS:
        if word in label_lower:
            return True

    return False  # Default: unknown = non-recyclable


# ── MOCK RESPONSE ────────────────────────────────────────────
def mock_response(reason="API unavailable"):
    """
    Returns a realistic demo response when API fails.
    Keeps the app running during presentations!
    """
    print(f"🔄 Using DEMO response ({reason})")
    return {
        "label"       : "Plastic Bottle",
        "confidence"  : 0.91,
        "recyclable"  : True,
        "emoji"       : "♻️",
        "category"    : "Plastic",
        "urdu_label"  : "پلاسٹک بوتل",
        "all_results" : [{"label": "Plastic Bottle", "confidence": 0.91}],
        "is_demo"     : True
    }


# ── URDU LABEL MAPPER ────────────────────────────────────────
def get_urdu_label(english_label):
    """
    Maps English waste labels to Urdu equivalents.
    Add more mappings as needed for your waste classes.
    """
    urdu_map = {
        "plastic bottle"  : "پلاسٹک بوتل",
        "plastic"         : "پلاسٹک",
        "paper"           : "کاغذ",
        "cardboard"       : "گتہ",
        "glass"           : "شیشہ",
        "metal"           : "دھات",
        "iron"            : "لوہا",
        "copper"          : "تانبا",
        "aluminium"       : "ایلومینیم",
        "battery"         : "بیٹری",
        "organic"         : "نامیاتی فضلہ",
        "food waste"      : "کھانے کا فضلہ",
        "e-waste"         : "الیکٹرانک فضلہ",
        "recyclable"      : "قابل ری سائیکل",
        "non-recyclable"  : "غیر قابل ری سائیکل",
        "scrap"           : "ردی",
        "default"         : "نامعلوم فضلہ"
    }

    label_lower = english_label.lower()
    for key, urdu in urdu_map.items():
        if key in label_lower:
            return urdu

    return urdu_map["default"]


# ── MAIN CLASSIFIER ──────────────────────────────────────────
def classify_waste(image_input):
    """
    Main function — sends image to Roboflow YOLO11 API
    and returns a full classification result.

    Args:
        image_input: file path (str), PIL Image, or bytes

    Returns:
        dict with keys:
            label       : English waste label
            urdu_label  : Urdu waste label
            confidence  : confidence score (0.0 to 1.0)
            recyclable  : True or False
            emoji       : ♻️ or 🗑️
            category    : broad waste category
            all_results : full list of predictions
            is_demo     : True if using mock response
    """
    print("\n🔍 Classifying waste image...")

    # Check if API key is configured
    if ROBOFLOW_API_KEY == "your_roboflow_api_key_here":
        print("⚠️  Roboflow API key not set — using demo response.")
        return mock_response("API key not configured")

    try:
        # Step 1: Prepare image
        img_base64, img_size = prepare_image(image_input)
        print(f"   ✅ Image prepared: {img_size[0]}x{img_size[1]} pixels")

        # Step 2: Call Roboflow API
        print("   ⏳ Calling Roboflow API...")
        response = requests.post(
            ROBOFLOW_API_URL,
            data    = img_base64,
            headers = {"Content-Type": "application/x-www-form-urlencoded"},
            timeout = 30
        )

        # Step 3: Handle errors
        if response.status_code == 404:
            print("   ❌ Model not found — check workspace/project/version.")
            return mock_response("Model not found (404)")

        if response.status_code == 401:
            print("   ❌ Invalid API key.")
            return mock_response("Invalid API key (401)")

        if response.status_code != 200:
            print(f"   ❌ API Error: {response.status_code} — {response.text}")
            return mock_response(f"API error {response.status_code}")

        # Step 4: Parse response
        data = response.json()
        print(f"   ✅ API responded!")

        # Roboflow classification response format:
        # {"predictions": [{"class": "Plastic", "confidence": 0.94}, ...]}
        predictions = data.get("predictions", [])

        if not predictions:
            print("   ⚠️  No predictions returned.")
            return mock_response("No predictions")

        # Get top prediction
        top         = predictions[0]
        label       = top.get("class", "Unknown")
        confidence  = round(top.get("confidence", 0.0), 3)
        recyclable  = is_recyclable(label)
        urdu_label  = get_urdu_label(label)

        result = {
            "label"       : label,
            "urdu_label"  : urdu_label,
            "confidence"  : confidence,
            "recyclable"  : recyclable,
            "emoji"       : "♻️" if recyclable else "🗑️",
            "category"    : label.split()[0] if label else "Unknown",
            "all_results" : predictions,
            "is_demo"     : False
        }

        print(f"   ✅ Result: {result['emoji']} {label} ({confidence * 100:.1f}% confident)")
        return result

    except requests.exceptions.Timeout:
        print("   ❌ Request timed out.")
        return mock_response("Timeout")

    except requests.exceptions.ConnectionError:
        print("   ❌ No internet connection.")
        return mock_response("No connection")

    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return mock_response(str(e))


# ── QUICK TEST ───────────────────────────────────────────────
def test_vision_module(image_path):
    """
    Quick test function — pass any image path to test.
    Shows full result in a readable format.
    """
    print("=" * 50)
    print("  🧪 VISION MODULE TEST")
    print("=" * 50)

    result = classify_waste(image_path)

    print(f"\n  {result['emoji']}  Label      : {result['label']}")
    print(f"  🇵🇰  Urdu Label  : {result['urdu_label']}")
    print(f"  📊  Confidence : {result['confidence'] * 100:.1f}%")
    print(f"  ♻️   Recyclable : {'YES ✅' if result['recyclable'] else 'NO ❌'}")
    print(f"  🔄  Demo Mode  : {'YES' if result['is_demo'] else 'NO'}")
    print("=" * 50)

    return result


# ── RUN DIRECTLY ─────────────────────────────────────────────
if __name__ == "__main__":
    # Change this to any image path to test
    TEST_IMAGE = "test_image.jpg"

    if os.path.exists(TEST_IMAGE):
        test_vision_module(TEST_IMAGE)
    else:
        print("⚠️  No test image found.")
        print("   Place an image called 'test_image.jpg' in the same folder.")
        print("   Running with mock response instead...\n")
        result = mock_response("No test image")
        print(f"   Demo result: {result['emoji']} {result['label']}")
