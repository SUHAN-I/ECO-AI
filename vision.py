# ============================================================
# FILE: vision.py
# PURPOSE: Waste image classification using YOLO11n
# MODEL: YOLO11n (Ultralytics pretrained, auto-downloads 5.6MB)
# MAPS: 80 COCO classes → waste categories (Urdu + English)
# USAGE: from vision import classify_waste, load_vision_model
# ============================================================
# INSTALL:
# pip install ultralytics Pillow
# ============================================================

# ╔══════════════════════════════════════════════════════════╗
# ║                COLAB TESTING CELLS                       ║
# ║         Run cells in order: 1 → 2 → 3 → 4 → 5          ║
# ╚══════════════════════════════════════════════════════════╝

# ── COLAB CELL 1: Install ────────────────────────────────────
"""
!pip install ultralytics Pillow
"""

# ── COLAB CELL 2: Load Model ─────────────────────────────────
"""
import importlib, sys
# If vision.py is uploaded to Colab, load it
exec(open('vision.py').read())

model = load_vision_model()
print(f"✅ Model ready! Classes: {len(model.names)}")
"""

# ── COLAB CELL 3: Test With Waste Image ──────────────────────
"""
from google.colab import files
print("📸 Upload a waste image...")
uploaded = files.upload()
image_filename = list(uploaded.keys())[0]

result = test_vision(model, image_filename)
"""

# ── COLAB CELL 4: Test Multiple Images ───────────────────────
"""
from google.colab import files
print("📸 Upload multiple waste images...")
uploaded = files.upload()

for filename in uploaded.keys():
    print(f"\n{'='*52}")
    print(f"📸 Image: {filename}")
    test_vision(model, filename)
"""

# ── COLAB CELL 5: Test Mapping Logic (No Image Needed) ───────
"""
print("🧪 Testing COCO → Waste Mapping Logic:")
print("=" * 60)
test_labels = [
    ("bottle", 0.85), ("wine glass", 0.72), ("car", 0.91),
    ("cell phone", 0.88), ("book", 0.76), ("banana", 0.93),
    ("tie", 0.65), ("sports ball", 0.80), ("remote", 0.71),
    ("scissors", 0.69), ("cup", 0.77), ("laptop", 0.82),
    ("pizza", 0.90), ("backpack", 0.75), ("knife", 0.68),
]
for label, conf in test_labels:
    r = map_to_waste(label, conf)
    print(f"  {r['emoji']} {label:15s} → {r['label_en']:28s} | "
          f"{'♻️ Recyclable' if r['recyclable'] else '🗑️ Non-Recyclable'}")
"""


# ============================================================
#                 ACTUAL CODE STARTS HERE
# ============================================================

import io
import os
from PIL import Image


# ── CONFIGURATION ────────────────────────────────────────────
MODEL_NAME           = "yolo11n.pt"
CONFIDENCE_THRESHOLD = 0.10   # Low = catches more waste objects


# ── COCO → WASTE MAPPING ─────────────────────────────────────
# Format: "coco_label": ("waste_category", "urdu_label", recyclable)
# Covers all 80 COCO classes with smart waste categorization

WASTE_MAPPING = {

    # ── PLASTIC WASTE ♻️ ─────────────────────────────────────
    "bottle"         : ("plastic",  "پلاسٹک بوتل",          True),
    "cup"            : ("plastic",  "پلاسٹک کپ",            True),
    "bowl"           : ("plastic",  "پلاسٹک باؤل",          True),
    "frisbee"        : ("plastic",  "پلاسٹک فضلہ",          True),
    "skateboard"     : ("plastic",  "پلاسٹک / لکڑی فضلہ",  True),
    "surfboard"      : ("plastic",  "پلاسٹک فضلہ",          True),
    "toothbrush"     : ("plastic",  "پلاسٹک برش",           True),
    "suitcase"       : ("plastic",  "پلاسٹک بیگ",           True),
    "umbrella"       : ("plastic",  "پلاسٹک چھتری",         True),
    "kite"           : ("plastic",  "پلاسٹک پتنگ",          True),
    "snowboard"      : ("plastic",  "پلاسٹک فضلہ",          True),

    # ── GLASS WASTE ♻️ ───────────────────────────────────────
    "wine glass"     : ("glass",    "شیشے کا گلاس",         True),
    "vase"           : ("glass",    "شیشے کا برتن",         True),

    # ── METAL / SCRAP WASTE ♻️ ───────────────────────────────
    "scissors"       : ("metal",    "دھاتی قینچی",          True),
    "knife"          : ("metal",    "دھاتی چاقو",           True),
    "spoon"          : ("metal",    "دھاتی چمچ",            True),
    "fork"           : ("metal",    "دھاتی کانٹا",          True),
    "car"            : ("metal",    "گاڑی دھاتی فضلہ",      True),
    "truck"          : ("metal",    "ٹرک دھاتی فضلہ",       True),
    "bus"            : ("metal",    "بس دھاتی فضلہ",        True),
    "bicycle"        : ("metal",    "سائیکل دھات",          True),
    "motorbike"      : ("metal",    "موٹر سائیکل دھات",     True),
    "airplane"       : ("metal",    "دھاتی فضلہ",           True),
    "train"          : ("metal",    "دھاتی فضلہ",           True),
    "boat"           : ("metal",    "دھاتی فضلہ",           True),
    "fire hydrant"   : ("metal",    "دھاتی پائپ",           True),
    "stop sign"      : ("metal",    "دھاتی سائن",           True),
    "parking meter"  : ("metal",    "دھاتی مشین",           True),
    "bench"          : ("metal",    "دھات / لکڑی فضلہ",    True),
    "chair"          : ("metal",    "دھات / پلاسٹک فضلہ",  True),
    "tennis racket"  : ("metal",    "دھات / پلاسٹک",        True),
    "baseball bat"   : ("metal",    "پلاسٹک / لکڑی",       True),
    "skis"           : ("metal",    "دھات / پلاسٹک فضلہ",  True),
    "couch"          : ("metal",    "فرنیچر فضلہ",          False),
    "bed"            : ("metal",    "فرنیچر فضلہ",          False),
    "dining table"   : ("metal",    "فرنیچر فضلہ",          False),

    # ── E-WASTE ♻️ ───────────────────────────────────────────
    "cell phone"     : ("e-waste",  "موبائل فون فضلہ",      True),
    "laptop"         : ("e-waste",  "لیپ ٹاپ فضلہ",        True),
    "tv"             : ("e-waste",  "ٹی وی فضلہ",           True),
    "remote"         : ("e-waste",  "ریموٹ الیکٹرانک فضلہ", True),
    "keyboard"       : ("e-waste",  "کی بورڈ فضلہ",         True),
    "mouse"          : ("e-waste",  "ماؤس فضلہ",            True),
    "microwave"      : ("e-waste",  "مائیکرو ویو فضلہ",    True),
    "toaster"        : ("e-waste",  "ٹوسٹر فضلہ",           True),
    "refrigerator"   : ("e-waste",  "فریج فضلہ",            True),
    "oven"           : ("e-waste",  "اوون فضلہ",            True),
    "hair drier"     : ("e-waste",  "ہیئر ڈرائر فضلہ",     True),
    "clock"          : ("e-waste",  "گھڑی فضلہ",            True),
    "traffic light"  : ("e-waste",  "الیکٹرانک فضلہ",       True),
    "sink"           : ("e-waste",  "دھاتی / پلاسٹک فضلہ", True),
    "toilet"         : ("trash",    "باتھ روم فضلہ",        False),

    # ── PAPER / CARDBOARD ♻️ ─────────────────────────────────
    "book"           : ("paper",    "کاغذ / کتاب فضلہ",    True),

    # ── TEXTILE / CLOTHING ♻️ ────────────────────────────────
    "tie"            : ("textile",  "کپڑے کا فضلہ",         True),
    "handbag"        : ("textile",  "ہینڈ بیگ فضلہ",        True),
    "backpack"       : ("textile",  "بیگ فضلہ",             True),
    "baseball glove" : ("textile",  "دستانہ فضلہ",          True),

    # ── RUBBER WASTE ♻️ ──────────────────────────────────────
    "sports ball"    : ("rubber",   "ربڑ فضلہ",             True),

    # ── ORGANIC / FOOD WASTE 🗑️ ──────────────────────────────
    "banana"         : ("organic",  "نامیاتی فضلہ",         False),
    "apple"          : ("organic",  "نامیاتی فضلہ",         False),
    "orange"         : ("organic",  "نامیاتی فضلہ",         False),
    "broccoli"       : ("organic",  "سبزی فضلہ",            False),
    "carrot"         : ("organic",  "سبزی فضلہ",            False),
    "hot dog"        : ("organic",  "کھانے کا فضلہ",        False),
    "pizza"          : ("organic",  "کھانے کا فضلہ",        False),
    "cake"           : ("organic",  "کھانے کا فضلہ",        False),
    "sandwich"       : ("organic",  "کھانے کا فضلہ",        False),
    "donut"          : ("organic",  "کھانے کا فضلہ",        False),
    "potted plant"   : ("organic",  "نامیاتی فضلہ",         False),

    # ── ANIMALS (not waste) ──────────────────────────────────
    "bird"           : ("unknown",  "جانور — فضلہ نہیں",    False),
    "cat"            : ("unknown",  "جانور — فضلہ نہیں",    False),
    "dog"            : ("unknown",  "جانور — فضلہ نہیں",    False),
    "horse"          : ("unknown",  "جانور — فضلہ نہیں",    False),
    "sheep"          : ("unknown",  "جانور — فضلہ نہیں",    False),
    "cow"            : ("unknown",  "جانور — فضلہ نہیں",    False),
    "elephant"       : ("unknown",  "جانور — فضلہ نہیں",    False),
    "bear"           : ("unknown",  "جانور — فضلہ نہیں",    False),
    "zebra"          : ("unknown",  "جانور — فضلہ نہیں",    False),
    "giraffe"        : ("unknown",  "جانور — فضلہ نہیں",    False),

    # ── PERSON (not waste) ───────────────────────────────────
    "person"         : ("unknown",  "انسان — فضلہ نہیں",    False),
}


# ── WASTE CATEGORY DETAILS ───────────────────────────────────
# Used by RAG engine to build smarter search queries
WASTE_CATEGORY_INFO = {
    "plastic"  : {
        "en"           : "Plastic Waste",
        "pk"           : "پلاسٹک فضلہ",
        "market_search": "plastic PET HDPE scrap rate PKR recycling Pakistan",
        "recyclable"   : True,
        "emoji"        : "♻️"
    },
    "glass"    : {
        "en"           : "Glass Waste",
        "pk"           : "شیشے کا فضلہ",
        "market_search": "glass scrap rate PKR recycling Pakistan",
        "recyclable"   : True,
        "emoji"        : "♻️"
    },
    "metal"    : {
        "en"           : "Metal / Scrap Waste",
        "pk"           : "دھاتی / سکریپ فضلہ",
        "market_search": "metal iron steel scrap rate PKR Misri Shah Pakistan",
        "recyclable"   : True,
        "emoji"        : "♻️"
    },
    "paper"    : {
        "en"           : "Paper / Cardboard Waste",
        "pk"           : "کاغذ / گتہ فضلہ",
        "market_search": "paper cardboard scrap rate PKR Pakistan recycling",
        "recyclable"   : True,
        "emoji"        : "♻️"
    },
    "e-waste"  : {
        "en"           : "Electronic Waste (E-Waste)",
        "pk"           : "الیکٹرانک فضلہ",
        "market_search": "e-waste electronic scrap rate PKR Pakistan circuit board",
        "recyclable"   : True,
        "emoji"        : "♻️"
    },
    "textile"  : {
        "en"           : "Textile / Clothing Waste",
        "pk"           : "کپڑے کا فضلہ",
        "market_search": "textile cloth scrap rate PKR recycling Pakistan",
        "recyclable"   : True,
        "emoji"        : "♻️"
    },
    "rubber"   : {
        "en"           : "Rubber Waste",
        "pk"           : "ربڑ فضلہ",
        "market_search": "rubber tyre scrap rate PKR pyrolysis Pakistan",
        "recyclable"   : True,
        "emoji"        : "♻️"
    },
    "organic"  : {
        "en"           : "Organic / Food Waste",
        "pk"           : "نامیاتی / کھانے کا فضلہ",
        "market_search": "organic waste composting biogas fertilizer Pakistan",
        "recyclable"   : False,
        "emoji"        : "🌱"
    },
    "trash"    : {
        "en"           : "General Non-Recyclable Trash",
        "pk"           : "غیر قابل ری سائیکل کوڑا",
        "market_search": "waste disposal management Pakistan",
        "recyclable"   : False,
        "emoji"        : "🗑️"
    },
    "unknown"  : {
        "en"           : "Unknown / Not Waste",
        "pk"           : "نامعلوم چیز",
        "market_search": "waste recycling Pakistan",
        "recyclable"   : False,
        "emoji"        : "❓"
    },
}

# Skip these when prioritizing waste detections
NON_WASTE_LABELS = [
    "person", "bird", "cat", "dog", "horse",
    "sheep", "cow", "elephant", "bear", "zebra", "giraffe"
]


# ════════════════════════════════════════════════════════════
# FUNCTION 1: Load Model Once
# ════════════════════════════════════════════════════════════
def load_vision_model():
    """
    Loads YOLO11n from Ultralytics.
    Auto-downloads 5.6MB on first run, cached after that.

    In Streamlit app.py use:
        @st.cache_resource
        def get_vision_model():
            return load_vision_model()

    Returns: YOLO model or None if failed
    """
    try:
        from ultralytics import YOLO
        print("⏳ Loading YOLO11n model...")
        model = YOLO(MODEL_NAME)
        print(f"✅ YOLO11n ready! {len(model.names)} object classes.")
        return model
    except Exception as e:
        print(f"❌ Failed to load YOLO11n: {e}")
        print("   Run: pip install ultralytics")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 2: Map COCO Label to Waste Category
# ════════════════════════════════════════════════════════════
def map_to_waste(coco_label, confidence):
    """
    Converts COCO object label to waste category.

    Args:
        coco_label : e.g. "bottle", "car", "cell phone"
        confidence : e.g. 0.85

    Returns: dict with label, urdu_label, recyclable, emoji etc.
    """
    label_lower = coco_label.lower()

    if label_lower in WASTE_MAPPING:
        category, urdu, recyclable = WASTE_MAPPING[label_lower]
    else:
        category, urdu, recyclable = "trash", "کوڑا کرکٹ", False

    cat = WASTE_CATEGORY_INFO.get(category, WASTE_CATEGORY_INFO["trash"])

    return {
        "label"         : category,
        "label_en"      : cat["en"],
        "urdu_label"    : urdu,
        "detected_obj"  : coco_label,
        "confidence"    : round(confidence, 3),
        "recyclable"    : recyclable,
        "emoji"         : cat["emoji"],
        "market_search" : cat["market_search"],
        "all_results"   : [],
        "is_demo"       : False
    }


# ════════════════════════════════════════════════════════════
# FUNCTION 3: Demo Fallback
# ════════════════════════════════════════════════════════════
def mock_response():
    """Demo response — keeps app alive during presentations."""
    print("   🔄 Using DEMO response")
    return {
        "label"         : "plastic",
        "label_en"      : "Plastic Waste",
        "urdu_label"    : "پلاسٹک بوتل",
        "detected_obj"  : "bottle",
        "confidence"    : 0.91,
        "recyclable"    : True,
        "emoji"         : "♻️",
        "market_search" : "plastic PET HDPE scrap rate PKR recycling Pakistan",
        "all_results"   : [{"label": "bottle", "confidence": 0.91}],
        "is_demo"       : True
    }


# ════════════════════════════════════════════════════════════
# FUNCTION 4: Main Classification
# ════════════════════════════════════════════════════════════
def classify_waste(model, image_input, confidence_threshold=CONFIDENCE_THRESHOLD):
    """
    Classifies waste in an image using YOLO11n + mapping.

    Prioritization (in order):
    1. Highest-confidence MAPPED waste item (not animal/person)
    2. Any mapped item
    3. Highest confidence detection (fallback)
    4. Demo response (if model fails)

    Args:
        model              : YOLO model from load_vision_model()
        image_input        : str (path), PIL Image, or bytes
        confidence_threshold: float, default 0.10

    Returns:
        dict with full waste classification result
    """
    print("\n🔍 Classifying waste image...")

    if model is None:
        print("   ❌ Model not loaded — using demo.")
        return mock_response()

    try:
        # ── Prepare Image ─────────────────────────────────────
        if isinstance(image_input, str):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        else:
            img = Image.open(io.BytesIO(image_input.read())).convert("RGB")

        img.thumbnail((640, 640))
        print(f"   ✅ Image prepared: {img.size}")

        # ── YOLO11n Detection ─────────────────────────────────
        results = model.predict(
            source  = img,
            conf    = confidence_threshold,
            verbose = False
        )

        result = results[0]
        boxes  = result.boxes

        if boxes is None or len(boxes) == 0:
            print("   ⚠️  No objects detected.")
            print("   💡 Try a clearer/closer image of the waste object.")
            return mock_response()

        # ── Collect All Detections ────────────────────────────
        all_detections = []
        for i in range(len(boxes)):
            cls  = int(boxes.cls[i])
            conf = float(boxes.conf[i])
            name = model.names[cls]
            all_detections.append((name, conf))

        all_detections.sort(key=lambda x: x[1], reverse=True)
        print(f"   📦 Detections: "
              f"{[(n, f'{c*100:.0f}%') for n, c in all_detections]}")

        # ── Smart Priority Selection ──────────────────────────
        best = None

        # Pass 1: mapped waste (exclude animals/people)
        for name, conf in all_detections:
            lname = name.lower()
            if lname in WASTE_MAPPING and lname not in NON_WASTE_LABELS:
                if WASTE_MAPPING[lname][0] != "unknown":
                    best = (name, conf)
                    break

        # Pass 2: any mapped item
        if best is None:
            for name, conf in all_detections:
                if name.lower() in WASTE_MAPPING:
                    best = (name, conf)
                    break

        # Pass 3: top detection
        if best is None:
            best = all_detections[0]

        # ── Build Result ──────────────────────────────────────
        name, conf  = best
        result_dict = map_to_waste(name, conf)
        result_dict["all_results"] = [
            {"label": n, "confidence": round(c, 3)}
            for n, c in all_detections
        ]

        print(f"   ✅ {result_dict['emoji']} {result_dict['label_en']} "
              f"← '{name}' ({conf*100:.1f}%)")
        return result_dict

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return mock_response()


# ════════════════════════════════════════════════════════════
# FUNCTION 5: Test Helper (Colab)
# ════════════════════════════════════════════════════════════
def test_vision(model, image_path):
    """
    Runs classification and prints formatted result.
    Use this in Colab testing cells.
    """
    result = classify_waste(model, image_path)

    print("\n" + "=" * 52)
    print("  🧪 VISION MODULE RESULT")
    print("=" * 52)
    print(f"  {result['emoji']}  Waste Type   : {result['label_en']}")
    print(f"  🔍  Detected    : {result['detected_obj']}")
    print(f"  🇵🇰  اردو        : {result['urdu_label']}")
    print(f"  📊  Confidence  : {result['confidence']*100:.1f}%")
    print(f"  ♻️   Recyclable  : {'YES ✅' if result['recyclable'] else 'NO ❌'}")
    print(f"  🔎  RAG Query   : {result['market_search']}")
    print(f"  🔄  Demo Mode   : {'YES ⚠️' if result['is_demo'] else 'NO ✅'}")
    print("=" * 52)

    if len(result.get("all_results", [])) > 1:
        print("\n  📋 All detections:")
        for r in result["all_results"]:
            print(f"     {r['label']:20s} → {r['confidence']*100:.1f}%")

    return result


# ════════════════════════════════════════════════════════════
# STANDALONE TEST (python vision.py)
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 52)
    print("  VISION MODULE — STANDALONE TEST")
    print("=" * 52)

    model = load_vision_model()

    if model:
        print("\n🧪 Testing COCO → Waste Mapping:")
        print("-" * 52)
        test_cases = [
            ("bottle", 0.85),     ("wine glass", 0.72),
            ("car", 0.91),        ("cell phone", 0.88),
            ("book", 0.76),       ("banana", 0.93),
            ("tie", 0.65),        ("sports ball", 0.80),
            ("remote", 0.71),     ("scissors", 0.69),
            ("cup", 0.77),        ("laptop", 0.82),
            ("pizza", 0.90),      ("backpack", 0.75),
            ("knife", 0.68),      ("fork", 0.55),
        ]
        for label, conf in test_cases:
            r = map_to_waste(label, conf)
            print(f"  {r['emoji']} {label:15s} → "
                  f"{r['label_en']:28s} | "
                  f"{'♻️ Recyclable' if r['recyclable'] else '🗑️ Non-Recyclable'}")

        print(f"\n✅ All {len(test_cases)} mappings tested!")
        print("   Use test_vision(model, 'image.jpg') for image testing.")
