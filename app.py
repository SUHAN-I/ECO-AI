# ============================================================
# FILE: app.py
# PURPOSE: Main Streamlit UI — Eco AI Pakistan Waste Manager
# RUN: streamlit run app.py
# ============================================================
# INSTALL:
# pip install streamlit groq faiss-cpu sentence-transformers
#             gspread google-auth qdrant-client cloudinary Pillow
# ============================================================

import streamlit as st
import json
import io
from PIL import Image
from datetime import datetime

# ── PAGE CONFIG (must be FIRST Streamlit call) ───────────────
st.set_page_config(
    page_title            = "Eco AI — Pakistan Waste Manager",
    page_icon             = "♻️",
    layout                = "wide",
    initial_sidebar_state = "expanded"
)

# ════════════════════════════════════════════════════════════
# CUSTOM CSS
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

:root {
    --g-dark   : #0a3d0a;
    --g-mid    : #1a6b1a;
    --g-light  : #2db52d;
    --g-neon   : #39ff14;
    --cream    : #f5f0e8;
    --danger   : #e63946;
    --warning  : #f4a261;
    --shadow   : 0 4px 24px rgba(0,0,0,0.08);
    --radius   : 16px;
}

html, body, [class*="css"] {
    font-family : 'DM Sans', sans-serif;
    background  : #f4f7f4;
}

h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; }

/* Header */
.eco-header {
    background    : linear-gradient(135deg, #0a3d0a 0%, #1a6b1a 60%, #2db52d 100%);
    color         : white;
    padding       : 2rem 2.5rem;
    border-radius : var(--radius);
    margin-bottom : 1.5rem;
    position      : relative;
    overflow      : hidden;
}
.eco-header::after {
    content       : '♻';
    position      : absolute;
    right         : 2rem;
    top           : 50%;
    transform     : translateY(-50%);
    font-size     : 6rem;
    opacity       : 0.08;
    line-height   : 1;
}
.eco-header h1 {
    font-size     : 2rem !important;
    margin        : 0 !important;
    color         : white !important;
    letter-spacing: -0.5px;
}
.eco-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 0.95rem; }

/* Result Card */
.result-card {
    background    : white;
    border-radius : var(--radius);
    padding       : 1.6rem;
    box-shadow    : var(--shadow);
    border-left   : 5px solid var(--g-light);
    margin-bottom : 1rem;
}
.result-card.danger { border-left-color: var(--danger); }

/* AI Response */
.ai-box {
    background    : white;
    border-radius : var(--radius);
    padding       : 1.8rem 2rem;
    box-shadow    : var(--shadow);
    border-top    : 4px solid var(--g-light);
    line-height   : 1.9;
    font-size     : 0.95rem;
    margin-bottom : 1rem;
}

/* Section toggle button row */
.toggle-row {
    display         : flex;
    gap             : 0.6rem;
    flex-wrap       : wrap;
    margin          : 1.2rem 0;
}

/* Badges */
.badge-yes  { background:#d4edda; color:#155724; border-radius:20px; padding:0.25rem 0.9rem; font-size:0.82rem; font-weight:600; display:inline-block; }
.badge-no   { background:#f8d7da; color:#721c24; border-radius:20px; padding:0.25rem 0.9rem; font-size:0.82rem; font-weight:600; display:inline-block; }
.badge-demo { background:#fff3cd; color:#856404; border-radius:20px; padding:0.2rem 0.8rem;  font-size:0.75rem; font-weight:600; display:inline-block; border:1px solid #ffc107; }

/* Harm colours */
.h-low  { color:#28a745; font-weight:600; }
.h-med  { color:#e0a800; font-weight:600; }
.h-high { color:#fd7e14; font-weight:600; }
.h-vhi  { color:#dc3545; font-weight:600; }

/* Scan history item */
.hist-item {
    background    : white;
    border-radius : 10px;
    padding       : 0.75rem 1.1rem;
    margin-bottom : 0.5rem;
    box-shadow    : 0 2px 8px rgba(0,0,0,0.05);
    display       : flex;
    align-items   : center;
    gap           : 0.8rem;
}

/* Nearby card */
.nearby-card {
    background    : white;
    border-radius : 12px;
    padding       : 1rem 1.2rem;
    margin-bottom : 0.6rem;
    box-shadow    : 0 2px 10px rgba(0,0,0,0.06);
    border-left   : 4px solid var(--g-light);
}

/* Market table */
.mkt-row {
    display        : flex;
    justify-content: space-between;
    padding        : 0.5rem 0;
    border-bottom  : 1px solid #f0f0f0;
    font-size      : 0.9rem;
}
.mkt-row:last-child { border-bottom: none; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# CACHED RESOURCE LOADERS (load once at startup)
# ════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="🦙 Loading Vision AI…")
def get_vision_client():
    from vision import load_vision_client
    return load_vision_client(st.secrets["GROQ_API_KEY"])


@st.cache_resource(show_spinner="🧠 Loading RAG Engine…")
def get_rag():
    from rag_engine import load_rag_components
    return load_rag_components(st.secrets["GROQ_API_KEY"])


@st.cache_resource(show_spinner="🗄️ Connecting databases…")
def get_db():
    from database import load_db_clients
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


# ════════════════════════════════════════════════════════════
# BILINGUAL TEXT
# ════════════════════════════════════════════════════════════

UI = {
    "title"        : {"en": "🌿 Eco AI — Pakistan Waste Manager",
                      "ur": "🌿 ایکو اے آئی — پاکستان ویسٹ مینیجر"},
    "subtitle"     : {"en": "Scan waste • Recycling guide • PKR market rates",
                      "ur": "کچرا اسکین • ری سائیکلنگ گائیڈ • PKR مارکیٹ ریٹ"},
    "cam_tab"      : {"en": "📷 Camera",         "ur": "📷 کیمرہ"},
    "upl_tab"      : {"en": "📁 Upload",          "ur": "📁 اپلوڈ"},
    "cam_label"    : {"en": "Take photo of waste","ur": "کچرے کی تصویر لیں"},
    "upl_label"    : {"en": "Upload waste image", "ur": "کچرے کی تصویر اپلوڈ کریں"},
    "analyse"      : {"en": "🔍 Analyse Waste",   "ur": "🔍 کچرہ تجزیہ کریں"},
    "ai_guide"     : {"en": "📝 AI Recycling & Business Guide",
                      "ur": "📝 اے آئی ری سائیکلنگ و کاروبار گائیڈ"},
    "followup_ph"  : {"en": "💬 Ask a follow-up question…",
                      "ur": "💬 مزید سوال پوچھیں…"},
    "ask"          : {"en": "Ask",  "ur": "پوچھیں"},
    "yes"          : {"en": "YES ✅","ur": "ہاں ✅"},
    "no"           : {"en": "NO ❌", "ur": "نہیں ❌"},
    "category"     : {"en": "Category",    "ur": "کیٹیگری"},
    "recyclable"   : {"en": "Recyclable",  "ur": "قابل ری سائیکل"},
    "harm"         : {"en": "Harm Level",  "ur": "نقصان"},
    "conf"         : {"en": "Confidence",  "ur": "اعتماد"},
    "reasoning"    : {"en": "Reasoning",   "ur": "وجہ"},
    "btn_nearby"   : {"en": "📍 Nearby Scans",      "ur": "📍 قریبی اسکین"},
    "btn_history"  : {"en": "📋 Scan History",       "ur": "📋 اسکین تاریخ"},
    "btn_market"   : {"en": "💰 Market Prices",      "ur": "💰 مارکیٹ ریٹ"},
    "btn_stats"    : {"en": "📊 Waste Stats",        "ur": "📊 اعداد و شمار"},
    "no_loc"       : {"en": "Enter GPS in sidebar for this feature.",
                      "ur": "یہ فیچر استعمال کریں تو سائیڈبار میں GPS درج کریں۔"},
    "saved"        : {"en": "✅ Scan saved!",  "ur": "✅ اسکین محفوظ!"},
    "city"         : {"en": "City",           "ur": "شہر"},
    "lat"          : {"en": "Latitude",       "ur": "عرض بلد"},
    "lng"          : {"en": "Longitude",      "ur": "طول بلد"},
    "demo"         : {"en": "⚠️ Demo Mode",   "ur": "⚠️ ڈیمو موڈ"},
    "sources"      : {"en": "📚 Knowledge sources used", "ur": "📚 ماخذ"},
    "no_scans"     : {"en": "No scans saved yet.",
                      "ur": "ابھی تک کوئی اسکین محفوظ نہیں۔"},
    "no_nearby"    : {"en": "No nearby scans found.",
                      "ur": "قریب کوئی اسکین نہیں ملا۔"},
}

def t(key, lang):
    """Return translated string."""
    code = "ur" if lang == "urdu" else "en"
    return UI.get(key, {}).get(code, key)


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

HARM_MAP = {
    "low"      : ('<span class="h-low">🟢 Low</span>',       '<span class="h-low">🟢 کم</span>'),
    "medium"   : ('<span class="h-med">🟡 Medium</span>',    '<span class="h-med">🟡 درمیانہ</span>'),
    "high"     : ('<span class="h-high">🟠 High</span>',     '<span class="h-high">🟠 زیادہ</span>'),
    "very high": ('<span class="h-vhi">🔴 Very High</span>', '<span class="h-vhi">🔴 بہت زیادہ</span>'),
}

MARKET_RATES = {
    "plastic"  : ("PKR 60–140 / kg",  "پلاسٹک PET/HDPE"),
    "glass"    : ("PKR 15–40 / kg",   "شیشہ"),
    "metal"    : ("PKR 80–350 / kg",  "دھات / آئرن / ایلومینیم"),
    "paper"    : ("PKR 20–55 / kg",   "کاغذ / اخبار"),
    "cardboard": ("PKR 25–60 / kg",   "گتہ"),
    "e-waste"  : ("PKR 200–800 / kg", "الیکٹرانک فضلہ"),
    "textile"  : ("PKR 30–120 / kg",  "کپڑے / فیبرک"),
    "rubber"   : ("PKR 40–90 / kg",   "ربڑ / ٹائر"),
    "organic"  : ("Compost / Biogas", "نامیاتی فضلہ"),
    "hazardous": ("Special disposal", "خطرناک فضلہ"),
    "trash"    : ("Landfill",         "کوڑا"),
}

def harm_html(level, lang):
    idx  = 1 if lang == "urdu" else 0
    key  = level.lower().replace(" ", "")
    row  = HARM_MAP.get(key, HARM_MAP["medium"])
    return row[idx]

def toggle_key(name):
    """Return session_state key for a toggle."""
    return f"show_{name}"

def init_toggles():
    """Initialise all toggle states to False."""
    for key in ["nearby", "history", "market", "stats"]:
        if toggle_key(key) not in st.session_state:
            st.session_state[toggle_key(key)] = False


# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown("## ♻️ Eco AI")
        st.markdown("---")

        # Language
        st.markdown("### 🌐 Language / زبان")
        language = st.radio(
            "lang", ["english", "urdu"],
            format_func      = lambda x: "🇬🇧 English" if x == "english" else "🇵🇰 اردو",
            horizontal       = True,
            label_visibility = "collapsed"
        )
        st.markdown("---")

        # GPS
        st.markdown("### 📍 Location")
        city = st.text_input(t("city", language), value="Lahore",
                             placeholder="Lahore, Karachi…")
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input(t("lat", language), value=31.5204,
                                  format="%.4f", step=0.0001)
        with c2:
            lng = st.number_input(t("lng", language), value=74.3587,
                                  format="%.4f", step=0.0001)
        st.markdown("---")

        # Today's stats
        st.markdown("### 📊 Stats")
        try:
            db     = get_db()
            from database import get_recent_scans
            recent = get_recent_scans(db, limit=100)
            today  = datetime.now().strftime("%Y-%m-%d")
            today_n = sum(1 for s in recent
                          if s.get("timestamp","").startswith(today))
            st.metric("Scans today", today_n)
            st.metric("Total saved", len(recent))
        except:
            st.metric("Scans today", "—")
            st.metric("Total saved",  "—")
        st.markdown("---")

        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
**Eco AI** turns Pakistan's waste into wealth.
- 🦙 Llama 4 Scout Vision
- 🤖 Llama 3.3-70B (Groq)
- 🔍 FAISS vector search
- 🗄️ Google Sheets + Qdrant
- 🖼️ Cloudinary image storage
            """)

    return language, city, lat, lng


# ════════════════════════════════════════════════════════════
# SECTION RENDERERS
# ════════════════════════════════════════════════════════════

def section_nearby(db, lat, lng, lang):
    st.markdown("---")
    st.markdown("#### 📍 " + t("btn_nearby", lang))
    if lat == 0.0 and lng == 0.0:
        st.warning(t("no_loc", lang))
        return
    with st.spinner("Searching nearby…"):
        from database import get_nearby_scans
        scans = get_nearby_scans(db, lat, lng, limit=10)
    if not scans:
        st.info(t("no_nearby", lang))
        return
    st.success(f"Found **{len(scans)}** nearby scans")
    for s in scans:
        emoji = "♻️" if s.get("recyclable") else "🗑️"
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            st.markdown(f"""
            <div class="nearby-card">
                <strong>{emoji} {s.get('waste_type','?').title()}</strong><br>
                <small style="color:#666">📍 {s.get('address','?')}</small>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"🏷️ `{s.get('category','?')}`")
            st.caption(s.get("timestamp","")[:10])
        with c3:
            if s.get("image_url"):
                st.image(s["image_url"], width=70)


def section_history(db, lang):
    st.markdown("---")
    st.markdown("#### 📋 " + t("btn_history", lang))
    with st.spinner("Loading history…"):
        from database import get_recent_scans
        rows = get_recent_scans(db, limit=20)
    if not rows:
        st.info(t("no_scans", lang))
        return
    cols = st.columns([2, 2, 1, 1, 1])
    for label in ["Waste Type", "Category", "Recyclable", "City", "Date"]:
        cols[["Waste Type","Category","Recyclable","City","Date"].index(label)]\
            .markdown(f"**{label}**")
    st.markdown("<hr style='margin:0.3rem 0'>", unsafe_allow_html=True)
    for row in rows:
        recyc  = row.get("recyclable","").lower() == "true"
        emoji  = "♻️" if recyc else "🗑️"
        c1,c2,c3,c4,c5 = st.columns([2,2,1,1,1])
        c1.markdown(f"{emoji} {row.get('waste_type','—').title()}")
        c2.markdown(f"`{row.get('category','—')}`")
        c3.markdown("✅" if recyc else "❌")
        c4.markdown(row.get("city","—"))
        c5.caption(row.get("timestamp","—")[:10])


def section_market(lang):
    st.markdown("---")
    st.markdown("#### 💰 " + t("btn_market", lang))
    st.caption("Reference rates — Misri Shah Lahore & Karachi scrap markets")
    st.markdown("<div style='background:white;border-radius:12px;padding:1.2rem;box-shadow:0 2px 12px rgba(0,0,0,0.07)'>",
                unsafe_allow_html=True)
    for cat, (rate, urdu) in MARKET_RATES.items():
        label = urdu if lang == "urdu" else cat.title()
        st.markdown(f"""
        <div class="mkt-row">
            <span>{label}</span>
            <strong style="color:#1a6b1a">{rate}</strong>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("⚠️ Rates are approximate. Verify with local dealers.")


def section_stats(db, lang):
    st.markdown("---")
    st.markdown("#### 📊 " + t("btn_stats", lang))
    try:
        from database import get_recent_scans
        rows = get_recent_scans(db, limit=200)
        if not rows:
            st.info(t("no_scans", lang))
            return

        # Count by category
        cats = {}
        recyclable_count = 0
        for row in rows:
            cat = row.get("category", "unknown")
            cats[cat] = cats.get(cat, 0) + 1
            if row.get("recyclable","").lower() == "true":
                recyclable_count += 1

        total = len(rows)

        # Top metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Scans",    total)
        m2.metric("Recyclable",     recyclable_count)
        m3.metric("Non-Recyclable", total - recyclable_count)
        m4.metric("Categories",     len(cats))

        # Bar chart
        if cats:
            import pandas as pd
            df = (pd.DataFrame(list(cats.items()), columns=["Category", "Count"])
                    .sort_values("Count", ascending=False))
            st.bar_chart(df.set_index("Category"))

    except Exception as e:
        st.error(f"Stats error: {e}")


# ════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════

def main():
    init_toggles()
    language, city, lat, lng = render_sidebar()

    # ── Header ───────────────────────────────────────────────
    st.markdown(f"""
    <div class="eco-header">
        <h1>{t('title', language)}</h1>
        <p>{t('subtitle', language)}</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Load clients ──────────────────────────────────────────
    vclient    = get_vision_client()
    components = get_rag()
    db         = get_db()

    # ── Image Input Tabs ──────────────────────────────────────
    tab1, tab2 = st.tabs([t("cam_tab", language), t("upl_tab", language)])
    image_bytes = None

    with tab1:
        cam = st.camera_input(t("cam_label", language),
                              label_visibility="collapsed")
        if cam:
            image_bytes = cam.getvalue()

    with tab2:
        upl = st.file_uploader(t("upl_label", language),
                               type=["jpg","jpeg","png","webp"],
                               label_visibility="collapsed")
        if upl:
            image_bytes = upl.getvalue()
            st.image(image_bytes, width=320)

    # ── Analyse Button ────────────────────────────────────────
    if image_bytes:
        col_btn, col_space = st.columns([1, 3])
        with col_btn:
            analyse = st.button(t("analyse", language),
                                type="primary",
                                use_container_width=True)

        if analyse or st.session_state.get("last_vision"):

            # ── Run Vision (only if new image) ────────────────
            if analyse:
                with st.spinner("🦙 Analysing image…"):
                    from vision import classify_waste
                    vision_result = classify_waste(vclient, image_bytes)
                st.session_state["last_vision"]  = vision_result
                st.session_state["last_image"]   = image_bytes
                st.session_state["rag_result"]   = None  # reset
                st.session_state["last_language"]= language

                # Auto-save scan to DB
                try:
                    from database import save_scan
                    save_scan(
                        db            = db,
                        vision_result = vision_result,
                        image_bytes   = image_bytes,
                        latitude      = lat,
                        longitude     = lng,
                        address       = f"{city}, Pakistan",
                        city          = city,
                        language      = language
                    )
                    st.toast(t("saved", language), icon="✅")
                except Exception as e:
                    st.toast(f"DB save error: {e}", icon="⚠️")

            vision_result = st.session_state.get("last_vision")
            if not vision_result:
                st.stop()

            # ── Result Card ───────────────────────────────────
            st.markdown("---")
            recyclable = vision_result.get("recyclable", False)
            card_cls   = "result-card" + ("" if recyclable else " danger")
            badge_cls  = "badge-yes" if recyclable else "badge-no"
            badge_txt  = t("yes", language) if recyclable else t("no", language)
            harm       = harm_html(vision_result.get("harmful_level","medium"), language)

            st.markdown(f"""
            <div class="{card_cls}">
                <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem">
                    <span style="font-size:2.8rem;line-height:1">{vision_result.get('emoji','♻️')}</span>
                    <div>
                        <div style="font-family:Syne,sans-serif;font-size:1.5rem;font-weight:800;color:#0a3d0a;line-height:1.1">
                            {vision_result.get('waste_type','Unknown').title()}
                        </div>
                        <div style="color:#666;font-size:0.95rem;margin-top:0.2rem">
                            {vision_result.get('urdu_label','نامعلوم')}
                        </div>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.8rem;margin-bottom:0.8rem">
                    <div>
                        <div style="font-size:0.7rem;color:#999;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.3rem">
                            {t('category', language)}
                        </div>
                        <strong>{vision_result.get('label_en','—')}</strong>
                    </div>
                    <div>
                        <div style="font-size:0.7rem;color:#999;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.3rem">
                            {t('recyclable', language)}
                        </div>
                        <span class="{badge_cls}">{badge_txt}</span>
                    </div>
                    <div>
                        <div style="font-size:0.7rem;color:#999;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.3rem">
                            {t('harm', language)}
                        </div>
                        {harm}
                    </div>
                    <div>
                        <div style="font-size:0.7rem;color:#999;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.3rem">
                            {t('conf', language)}
                        </div>
                        <strong>{vision_result.get('confidence','—').upper()}</strong>
                    </div>
                </div>
                <div style="font-size:0.85rem;color:#555;font-style:italic;border-top:1px solid #f0f0f0;padding-top:0.6rem">
                    💬 {vision_result.get('reasoning','')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if vision_result.get("is_demo"):
                st.markdown('<span class="badge-demo">⚠️ Demo Mode</span>',
                            unsafe_allow_html=True)

            # ── Run RAG ───────────────────────────────────────
            if st.session_state.get("rag_result") is None:
                with st.spinner("🤖 Generating recycling guide…"):
                    from rag_engine import run_rag_pipeline
                    rag_result = run_rag_pipeline(
                        components    = components,
                        vision_result = vision_result,
                        language      = language
                    )
                st.session_state["rag_result"] = rag_result
            else:
                rag_result = st.session_state["rag_result"]

            # ── AI Guide ──────────────────────────────────────
            st.markdown(f"### {t('ai_guide', language)}")
            st.markdown(f"""
            <div class="ai-box">
                {rag_result['answer'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

            if rag_result.get("is_demo"):
                st.markdown('<span class="badge-demo">⚠️ Demo Mode</span>',
                            unsafe_allow_html=True)

            # Sources
            if rag_result.get("sources_used"):
                with st.expander(t("sources", language)):
                    for src in rag_result["sources_used"]:
                        st.markdown(f"- `{src}`")
                    st.caption(f"Chunks used: {rag_result.get('chunks_used',0)}")

            # ── Follow-up Question ────────────────────────────
            st.markdown("---")
            fc1, fc2 = st.columns([5, 1])
            with fc1:
                followup = st.text_input(
                    t("followup_ph", language),
                    key              = "followup_q",
                    label_visibility = "collapsed",
                    placeholder      = t("followup_ph", language)
                )
            with fc2:
                ask_btn = st.button(t("ask", language),
                                    use_container_width=True)

            if ask_btn and followup.strip():
                with st.spinner("🤖 Answering…"):
                    from rag_engine import run_rag_pipeline
                    fup = run_rag_pipeline(
                        components    = components,
                        vision_result = vision_result,
                        user_question = followup,
                        language      = language
                    )
                st.markdown(f"""
                <div class="ai-box" style="border-top-color:#1a6b1a">
                    <strong>Q: {followup}</strong><br><br>
                    {fup['answer'].replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

            # ════════════════════════════════════════════════
            # TOGGLE BUTTONS ROW
            # ════════════════════════════════════════════════
            st.markdown("---")
            st.markdown("### 🔽 " + ("Explore More" if language == "english" else "مزید دیکھیں"))

            b1, b2, b3, b4 = st.columns(4)

            with b1:
                if st.button(
                    t("btn_nearby", language),
                    use_container_width = True,
                    type = "secondary" if not st.session_state[toggle_key("nearby")] else "primary"
                ):
                    st.session_state[toggle_key("nearby")] = \
                        not st.session_state[toggle_key("nearby")]
                    st.rerun()

            with b2:
                if st.button(
                    t("btn_history", language),
                    use_container_width = True,
                    type = "secondary" if not st.session_state[toggle_key("history")] else "primary"
                ):
                    st.session_state[toggle_key("history")] = \
                        not st.session_state[toggle_key("history")]
                    st.rerun()

            with b3:
                if st.button(
                    t("btn_market", language),
                    use_container_width = True,
                    type = "secondary" if not st.session_state[toggle_key("market")] else "primary"
                ):
                    st.session_state[toggle_key("market")] = \
                        not st.session_state[toggle_key("market")]
                    st.rerun()

            with b4:
                if st.button(
                    t("btn_stats", language),
                    use_container_width = True,
                    type = "secondary" if not st.session_state[toggle_key("stats")] else "primary"
                ):
                    st.session_state[toggle_key("stats")] = \
                        not st.session_state[toggle_key("stats")]
                    st.rerun()

            # ── Render toggled sections ───────────────────────
            if st.session_state[toggle_key("nearby")]:
                section_nearby(db, lat, lng, language)

            if st.session_state[toggle_key("history")]:
                section_history(db, language)

            if st.session_state[toggle_key("market")]:
                section_market(language)

            if st.session_state[toggle_key("stats")]:
                section_stats(db, language)

    else:
        # ── Empty State ───────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#aaa">
            <div style="font-size:4rem;margin-bottom:1rem">📸</div>
            <div style="font-family:Syne,sans-serif;font-size:1.2rem;color:#888">
                Take a photo or upload a waste image to get started
            </div>
            <div style="margin-top:0.5rem;color:#bbb;font-size:0.9rem">
                کچرے کی تصویر لیں یا اپلوڈ کریں
            </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
