# ============================================================
# FILE: database.py
# PURPOSE: All data storage and retrieval
#   - Google Sheets  → scan logs + user data
#   - Qdrant Cloud   → GPS coordinates + nearby search
#   - Cloudinary     → waste image storage + retrieval
# USAGE: from database import load_db_clients, save_scan, get_nearby_scans
# ============================================================
# INSTALL:
# pip install gspread google-auth qdrant-client cloudinary
# ============================================================

# ╔══════════════════════════════════════════════════════════╗
# ║                COLAB TESTING CELLS                       ║
# ║         Run cells in order: 1 → 2 → 3 → 4 → 5          ║
# ╚══════════════════════════════════════════════════════════╝

# ── COLAB CELL 1: Install ────────────────────────────────────
"""
!pip install gspread google-auth qdrant-client cloudinary -q
"""

# ── COLAB CELL 2: Load All DB Clients ────────────────────────
"""
exec(open('database.py').read())

# Your credentials
GSHEET_ID    = "1bJwCrPW0EJ8aDvpXuAooygXzZW0dygw6K1t4c2p1FTM"
GSHEET_CREDS = { ...your service account dict... }
QDRANT_URL   = "https://your-cluster.qdrant.io"
QDRANT_KEY   = "your-qdrant-key"
CLD_NAME     = "your-cloud-name"
CLD_KEY      = "your-api-key"
CLD_SECRET   = "your-api-secret"

db = load_db_clients(
    gsheet_id          = GSHEET_ID,
    gsheet_credentials = GSHEET_CREDS,
    qdrant_url         = QDRANT_URL,
    qdrant_api_key     = QDRANT_KEY,
    cloudinary_name    = CLD_NAME,
    cloudinary_key     = CLD_KEY,
    cloudinary_secret  = CLD_SECRET
)
print("✅ All DB clients ready!")
"""

# ── COLAB CELL 3: Test Full Save Scan ────────────────────────
"""
from PIL import Image
import io

# Mock vision result
mock_vision = {
    "waste_type"   : "aluminium can",
    "label"        : "metal",
    "label_en"     : "Metal / Scrap Waste",
    "urdu_label"   : "ایلومینیم ڈب",
    "recyclable"   : True,
    "harmful_level": "low",
    "confidence"   : "high",
}

# Mock image (use real image in app)
img = Image.new("RGB", (200, 200), color=(180, 180, 180))
buf = io.BytesIO()
img.save(buf, format="JPEG")
image_bytes = buf.getvalue()

# Save everything
result = save_scan(
    db            = db,
    vision_result = mock_vision,
    image_bytes   = image_bytes,
    latitude      = 31.5204,
    longitude     = 74.3587,
    address       = "Misri Shah, Lahore",
    city          = "Lahore",
    language      = "english"
)

print(f"\\n✅ Full scan saved!")
print(f"   Image URL   : {result['image_url']}")
print(f"   Sheets row  : {result['sheets_row']}")
print(f"   Qdrant ID   : {result['qdrant_id']}")
"""

# ── COLAB CELL 4: Test Nearby Search ─────────────────────────
"""
nearby = get_nearby_scans(
    db        = db,
    latitude  = 31.5204,
    longitude = 74.3587,
    limit     = 5
)

print(f"\\n📍 Nearby waste scans: {len(nearby)}")
for scan in nearby:
    print(f"   → {scan['waste_type']} at {scan['address']} | {scan['image_url']}")
"""

# ── COLAB CELL 5: Test Get Recent Scans ──────────────────────
"""
recent = get_recent_scans(db, limit=5)

print(f"\\n📋 Recent scans: {len(recent)}")
for scan in recent:
    print(f"   → {scan}")
"""


# ============================================================
#                 ACTUAL CODE STARTS HERE
# ============================================================

import os
import io
import uuid
from datetime import datetime


# ── CONFIGURATION ────────────────────────────────────────────
GSHEET_SCOPES      = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SCAN_LOGS_SHEET    = "scan_logs"        # Sheet 1 tab name
LOCATIONS_SHEET    = "user_locations"   # Sheet 2 tab name
QDRANT_COLLECTION  = "waste_locations"  # Qdrant collection name
QDRANT_VECTOR_SIZE = 2                  # lat, lng = 2D vector
CLOUDINARY_FOLDER  = "waste_app/scans"  # Cloudinary folder


# ════════════════════════════════════════════════════════════
# FUNCTION 1: Load All DB Clients (once at startup)
# ════════════════════════════════════════════════════════════
def load_db_clients(gsheet_id, gsheet_credentials,
                    qdrant_url, qdrant_api_key,
                    cloudinary_name, cloudinary_key, cloudinary_secret):
    """
    Initializes all database clients at app startup.
    Call this ONCE — wrap in @st.cache_resource in Streamlit.

    In Streamlit app.py:
        @st.cache_resource
        def get_db_clients():
            import json
            creds = json.loads(st.secrets["GSHEET_CREDENTIALS"])
            return load_db_clients(
                gsheet_id          = st.secrets["GSHEET_ID"],
                gsheet_credentials = creds,
                qdrant_url         = st.secrets["QDRANT_URL"],
                qdrant_api_key     = st.secrets["QDRANT_API_KEY"],
                cloudinary_name    = st.secrets["CLOUDINARY_CLOUD_NAME"],
                cloudinary_key     = st.secrets["CLOUDINARY_API_KEY"],
                cloudinary_secret  = st.secrets["CLOUDINARY_API_SECRET"]
            )

    Returns:
        dict with all client objects + config
    """
    import gspread
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    from google.oauth2.service_account import Credentials
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance

    print("⏳ Loading database clients...")
    db = {}

    # ── Google Sheets ─────────────────────────────────────────
    try:
        print("   Connecting to Google Sheets...")
        creds         = Credentials.from_service_account_info(
            gsheet_credentials, scopes=GSHEET_SCOPES
        )
        gc            = gspread.authorize(creds)
        sheet         = gc.open_by_key(gsheet_id)
        db["sheet"]   = sheet
        db["gsheet_id"] = gsheet_id
        print(f"   ✅ Google Sheets: '{sheet.title}' connected")
    except Exception as e:
        print(f"   ❌ Google Sheets failed: {e}")
        db["sheet"] = None

    # ── Qdrant ────────────────────────────────────────────────
    try:
        print("   Connecting to Qdrant...")
        qdrant      = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        collections = [c.name for c in qdrant.get_collections().collections]

        # Create collection if it doesn't exist
        if QDRANT_COLLECTION not in collections:
            qdrant.create_collection(
                collection_name = QDRANT_COLLECTION,
                vectors_config  = VectorParams(
                    size     = QDRANT_VECTOR_SIZE,
                    distance = Distance.EUCLID
                )
            )
            print(f"   ✅ Qdrant: collection '{QDRANT_COLLECTION}' created")
        else:
            print(f"   ✅ Qdrant: collection '{QDRANT_COLLECTION}' ready")

        db["qdrant"] = qdrant

    except Exception as e:
        print(f"   ❌ Qdrant failed: {e}")
        db["qdrant"] = None

    # ── Cloudinary ────────────────────────────────────────────
    try:
        print("   Connecting to Cloudinary...")
        cloudinary.config(
            cloud_name = cloudinary_name,
            api_key    = cloudinary_key,
            api_secret = cloudinary_secret,
            secure     = True
        )
        # Quick test
        cloudinary.api.ping()
        db["cloudinary_configured"] = True
        print(f"   ✅ Cloudinary: '{cloudinary_name}' connected")
    except Exception as e:
        print(f"   ❌ Cloudinary failed: {e}")
        db["cloudinary_configured"] = False

    # ── Summary ───────────────────────────────────────────────
    all_ok = all([
        db.get("sheet")               is not None,
        db.get("qdrant")              is not None,
        db.get("cloudinary_configured")
    ])

    status = "✅ All database clients loaded!" if all_ok else "⚠️ Some clients failed"
    print(f"\n{status}")
    return db


# ════════════════════════════════════════════════════════════
# FUNCTION 2: Upload Image to Cloudinary
# ════════════════════════════════════════════════════════════
def upload_image(image_bytes, waste_type, scan_id):
    """
    Uploads a waste image to Cloudinary.
    Returns the secure URL for storing in Sheets + Qdrant.

    Args:
        image_bytes : raw image bytes (from camera or upload)
        waste_type  : e.g. "aluminium can" (used for tagging)
        scan_id     : unique ID for this scan

    Returns:
        secure URL string or None if failed
    """
    import cloudinary.uploader

    try:
        print(f"\n📸 Uploading image to Cloudinary...")

        result = cloudinary.uploader.upload(
            image_bytes,
            folder        = CLOUDINARY_FOLDER,
            public_id     = f"scan_{scan_id}",
            resource_type = "image",
            tags          = [
                "waste",
                waste_type.replace(" ", "_").lower(),
                "pakistan",
                "eco_ai_app"
            ],
            transformation = [
                {"width": 800, "height": 800, "crop": "limit"},  # Max 800px
                {"quality": "auto"}                               # Auto compress
            ]
        )

        url = result["secure_url"]
        print(f"   ✅ Image uploaded: {url}")
        return url

    except Exception as e:
        print(f"   ❌ Cloudinary upload failed: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 3: Save Scan to Google Sheets
# ════════════════════════════════════════════════════════════
def save_to_sheets(db, scan_data):
    """
    Saves a scan record to Google Sheets scan_logs tab.

    Columns:
    timestamp | waste_type | category | recyclable |
    harmful_level | confidence | language | city |
    address | latitude | longitude | image_url | scan_id

    Args:
        db        : db clients dict
        scan_data : dict with all scan info

    Returns:
        row number saved or None if failed
    """
    sheet = db.get("sheet")
    if sheet is None:
        print("   ⚠️ Google Sheets not available")
        return None

    try:
        ws = sheet.worksheet(SCAN_LOGS_SHEET)

        row = [
            scan_data.get("timestamp",     datetime.now().isoformat()),
            scan_data.get("waste_type",    "unknown"),
            scan_data.get("category",      "unknown"),
            scan_data.get("urdu_label",    "نامعلوم"),
            str(scan_data.get("recyclable", False)),
            scan_data.get("harmful_level", "medium"),
            scan_data.get("confidence",    "medium"),
            scan_data.get("language",      "english"),
            scan_data.get("city",          "unknown"),
            scan_data.get("address",       "unknown"),
            str(scan_data.get("latitude",  0.0)),
            str(scan_data.get("longitude", 0.0)),
            scan_data.get("image_url",     ""),
            scan_data.get("scan_id",       ""),
        ]

        ws.append_row(row)
        row_count = len(ws.get_all_values())
        print(f"   ✅ Sheets: saved to row {row_count}")
        return row_count

    except Exception as e:
        print(f"   ❌ Sheets save failed: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 4: Save GPS to Qdrant
# ════════════════════════════════════════════════════════════
def save_to_qdrant(db, scan_data):
    """
    Saves GPS location as a vector point in Qdrant.
    Enables nearby waste search using GPS coordinates.

    Vector = [latitude, longitude] (2D)
    Payload = full scan metadata for display

    Args:
        db        : db clients dict
        scan_data : dict with all scan info

    Returns:
        point ID or None if failed
    """
    from qdrant_client.models import PointStruct

    qdrant = db.get("qdrant")
    if qdrant is None:
        print("   ⚠️ Qdrant not available")
        return None

    try:
        lat = float(scan_data.get("latitude",  0.0))
        lng = float(scan_data.get("longitude", 0.0))

        # Use hash of scan_id as integer ID
        point_id = abs(hash(scan_data.get("scan_id", str(uuid.uuid4())))) % (10**9)

        qdrant.upsert(
            collection_name = QDRANT_COLLECTION,
            points=[
                PointStruct(
                    id      = point_id,
                    vector  = [lat, lng],
                    payload = {
                        "scan_id"      : scan_data.get("scan_id", ""),
                        "waste_type"   : scan_data.get("waste_type", "unknown"),
                        "category"     : scan_data.get("category", "unknown"),
                        "urdu_label"   : scan_data.get("urdu_label", "نامعلوم"),
                        "recyclable"   : scan_data.get("recyclable", False),
                        "harmful_level": scan_data.get("harmful_level", "medium"),
                        "timestamp"    : scan_data.get("timestamp", datetime.now().isoformat()),
                        "city"         : scan_data.get("city", "unknown"),
                        "address"      : scan_data.get("address", "unknown"),
                        "latitude"     : lat,
                        "longitude"    : lng,
                        "image_url"    : scan_data.get("image_url", ""),
                        "language"     : scan_data.get("language", "english"),
                    }
                )
            ]
        )

        print(f"   ✅ Qdrant: GPS point saved (ID: {point_id})")
        return point_id

    except Exception as e:
        print(f"   ❌ Qdrant save failed: {e}")
        return None


# ════════════════════════════════════════════════════════════
# FUNCTION 5: Main Save Scan (combines all 3)
# ════════════════════════════════════════════════════════════
def save_scan(db, vision_result, image_bytes=None,
              latitude=0.0, longitude=0.0,
              address="Unknown", city="Unknown",
              language="english"):
    """
    Saves a complete waste scan to all databases.

    Pipeline:
    1. Generate unique scan ID
    2. Upload image to Cloudinary → get URL
    3. Save scan log to Google Sheets
    4. Save GPS point to Qdrant

    Args:
        db            : db clients dict from load_db_clients()
        vision_result : dict from vision.py classify_waste()
        image_bytes   : raw image bytes (optional)
        latitude      : GPS latitude
        longitude     : GPS longitude
        address       : human readable address
        city          : city name
        language      : "english" or "urdu"

    Returns:
        dict with:
            scan_id   : unique ID for this scan
            image_url : Cloudinary URL
            sheets_row: Google Sheets row number
            qdrant_id : Qdrant point ID
            timestamp : when scan was saved
    """
    print(f"\n💾 Saving scan: {vision_result.get('waste_type', 'unknown')}")
    print("=" * 50)

    timestamp = datetime.now().isoformat()
    scan_id   = str(uuid.uuid4())[:8].upper()  # Short unique ID e.g. "A3F7B2C1"

    # ── Step 1: Upload Image ──────────────────────────────────
    image_url = None
    if image_bytes and db.get("cloudinary_configured"):
        image_url = upload_image(
            image_bytes = image_bytes,
            waste_type  = vision_result.get("waste_type", "waste"),
            scan_id     = scan_id
        )

    # ── Build Scan Data Dict ──────────────────────────────────
    scan_data = {
        "scan_id"      : scan_id,
        "timestamp"    : timestamp,
        "waste_type"   : vision_result.get("waste_type",    "unknown"),
        "category"     : vision_result.get("label",         "unknown"),
        "urdu_label"   : vision_result.get("urdu_label",    "نامعلوم"),
        "recyclable"   : vision_result.get("recyclable",    False),
        "harmful_level": vision_result.get("harmful_level", "medium"),
        "confidence"   : vision_result.get("confidence",    "medium"),
        "language"     : language,
        "city"         : city,
        "address"      : address,
        "latitude"     : float(latitude),
        "longitude"    : float(longitude),
        "image_url"    : image_url or "",
    }

    # ── Step 2: Save to Google Sheets ────────────────────────
    sheets_row = save_to_sheets(db, scan_data)

    # ── Step 3: Save to Qdrant ────────────────────────────────
    qdrant_id  = save_to_qdrant(db, scan_data)

    result = {
        "scan_id"   : scan_id,
        "timestamp" : timestamp,
        "image_url" : image_url or "",
        "sheets_row": sheets_row,
        "qdrant_id" : qdrant_id,
        "success"   : all([sheets_row, qdrant_id])
    }

    status = "✅" if result["success"] else "⚠️"
    print(f"\n{status} Scan saved!")
    print(f"   Scan ID    : {scan_id}")
    print(f"   Image URL  : {image_url or 'No image'}")
    print(f"   Sheets row : {sheets_row}")
    print(f"   Qdrant ID  : {qdrant_id}")
    return result


# ════════════════════════════════════════════════════════════
# FUNCTION 6: Get Nearby Waste Scans (Qdrant GPS search)
# ════════════════════════════════════════════════════════════
def get_nearby_scans(db, latitude, longitude, limit=10):
    """
    Finds nearby waste scans using GPS coordinates.
    Uses Qdrant vector search on [lat, lng] vectors.

    Args:
        db        : db clients dict
        latitude  : current GPS latitude
        longitude : current GPS longitude
        limit     : max number of results

    Returns:
        list of nearby scan dicts with image_url, waste_type etc.
    """
    qdrant = db.get("qdrant")
    if qdrant is None:
        print("⚠️ Qdrant not available")
        return []

    try:
        print(f"\n📍 Searching nearby scans ({latitude:.4f}, {longitude:.4f})...")

        results = qdrant.query_points(
            collection_name = QDRANT_COLLECTION,
            query           = [float(latitude), float(longitude)],
            limit           = limit
        )

        nearby = []
        for r in results.points:
            nearby.append({
                "scan_id"      : r.payload.get("scan_id",       ""),
                "waste_type"   : r.payload.get("waste_type",    "unknown"),
                "category"     : r.payload.get("category",      "unknown"),
                "urdu_label"   : r.payload.get("urdu_label",    "نامعلوم"),
                "recyclable"   : r.payload.get("recyclable",    False),
                "harmful_level": r.payload.get("harmful_level", "medium"),
                "timestamp"    : r.payload.get("timestamp",     ""),
                "address"      : r.payload.get("address",       "unknown"),
                "city"         : r.payload.get("city",          "unknown"),
                "latitude"     : r.payload.get("latitude",      0.0),
                "longitude"    : r.payload.get("longitude",     0.0),
                "image_url"    : r.payload.get("image_url",     ""),
                "distance"     : round(r.score, 4)
            })

        print(f"   ✅ Found {len(nearby)} nearby scans")
        return nearby

    except Exception as e:
        print(f"   ❌ Nearby search failed: {e}")
        return []


# ════════════════════════════════════════════════════════════
# FUNCTION 7: Get Recent Scans from Google Sheets
# ════════════════════════════════════════════════════════════
def get_recent_scans(db, limit=10):
    """
    Retrieves the most recent scan logs from Google Sheets.
    Used to show scan history in the app.

    Args:
        db    : db clients dict
        limit : max number of recent scans to return

    Returns:
        list of scan dicts (most recent first)
    """
    sheet = db.get("sheet")
    if sheet is None:
        print("⚠️ Google Sheets not available")
        return []

    try:
        print(f"\n📋 Getting {limit} recent scans from Sheets...")

        ws      = sheet.worksheet(SCAN_LOGS_SHEET)
        rows    = ws.get_all_values()

        if len(rows) <= 1:
            print("   No scans found yet")
            return []

        # Skip header row, get last N rows, reverse for newest first
        data_rows = rows[1:][-limit:][::-1]
        headers   = [
            "timestamp", "waste_type", "category", "urdu_label",
            "recyclable", "harmful_level", "confidence", "language",
            "city", "address", "latitude", "longitude",
            "image_url", "scan_id"
        ]

        scans = []
        for row in data_rows:
            # Pad row if shorter than headers
            padded = row + [""] * (len(headers) - len(row))
            scans.append(dict(zip(headers, padded)))

        print(f"   ✅ Retrieved {len(scans)} recent scans")
        return scans

    except Exception as e:
        print(f"   ❌ Get recent scans failed: {e}")
        return []


# ════════════════════════════════════════════════════════════
# FUNCTION 8: Get Images by Waste Category (Cloudinary)
# ════════════════════════════════════════════════════════════
def get_images_by_category(category, max_results=10):
    """
    Retrieves waste images from Cloudinary by category tag.
    Used to show visual examples of waste types.

    Args:
        category   : waste category (e.g. "plastic", "metal")
        max_results: max images to return

    Returns:
        list of image URL strings
    """
    import cloudinary.api

    try:
        print(f"\n🖼️ Getting '{category}' images from Cloudinary...")

        result = cloudinary.api.resources_by_tag(
            category.replace(" ", "_").lower(),
            max_results = max_results,
            resource_type="image"
        )

        urls = [r["secure_url"] for r in result.get("resources", [])]
        print(f"   ✅ Found {len(urls)} images for '{category}'")
        return urls

    except Exception as e:
        print(f"   ❌ Cloudinary search failed: {e}")
        return []


# ════════════════════════════════════════════════════════════
# STREAMLIT USAGE (in app.py)
# ════════════════════════════════════════════════════════════
"""
import streamlit as st
import json
from database import load_db_clients, save_scan, get_nearby_scans, get_recent_scans

@st.cache_resource
def get_db():
    creds = json.loads(st.secrets["GSHEET_CREDENTIALS"])
    return load_db_clients(
        gsheet_id          = st.secrets["GSHEET_ID"],
        gsheet_credentials = creds,
        qdrant_url         = st.secrets["QDRANT_URL"],
        qdrant_api_key     = st.secrets["QDRANT_API_KEY"],
        cloudinary_name    = st.secrets["CLOUDINARY_CLOUD_NAME"],
        cloudinary_key     = st.secrets["CLOUDINARY_API_KEY"],
        cloudinary_secret  = st.secrets["CLOUDINARY_API_SECRET"]
    )

db = get_db()

# Save a scan
if uploaded_image and vision_result:
    save_result = save_scan(
        db            = db,
        vision_result = vision_result,
        image_bytes   = uploaded_image.getvalue(),
        latitude      = user_lat,
        longitude     = user_lng,
        address       = user_address,
        city          = user_city,
        language      = selected_language
    )
    st.success(f"✅ Scan saved! ID: {save_result['scan_id']}")

# Get nearby scans
nearby = get_nearby_scans(db, user_lat, user_lng, limit=5)
for scan in nearby:
    st.image(scan['image_url'])
    st.write(f"{scan['waste_type']} — {scan['address']}")
"""


# ════════════════════════════════════════════════════════════
# STANDALONE TEST (python database.py)
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import json

    print("=" * 55)
    print("  DATABASE MODULE — STANDALONE TEST")
    print("=" * 55)

    # Load from environment variables
    GSHEET_ID    = os.getenv("GSHEET_ID", "")
    GSHEET_CREDS = json.loads(os.getenv("GSHEET_CREDENTIALS", "{}"))
    QDRANT_URL   = os.getenv("QDRANT_URL", "")
    QDRANT_KEY   = os.getenv("QDRANT_API_KEY", "")
    CLD_NAME     = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLD_KEY      = os.getenv("CLOUDINARY_API_KEY", "")
    CLD_SECRET   = os.getenv("CLOUDINARY_API_SECRET", "")

    db = load_db_clients(
        gsheet_id          = GSHEET_ID,
        gsheet_credentials = GSHEET_CREDS,
        qdrant_url         = QDRANT_URL,
        qdrant_api_key     = QDRANT_KEY,
        cloudinary_name    = CLD_NAME,
        cloudinary_key     = CLD_KEY,
        cloudinary_secret  = CLD_SECRET
    )

    # Test nearby search
    nearby = get_nearby_scans(db, 31.5204, 74.3587, limit=3)
    print(f"\nNearby scans: {len(nearby)}")

    # Test recent scans
    recent = get_recent_scans(db, limit=3)
    print(f"Recent scans: {len(recent)}")

    print("\n✅ Database module test complete!")
