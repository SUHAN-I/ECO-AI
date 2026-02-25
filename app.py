# ============================================================
# FILE: app.py — Eco AI Pakistan Waste Manager
# RUN:  streamlit run app.py
# ============================================================

import streamlit as st
import json, uuid
from datetime import datetime
import io
from PIL import Image


st.set_page_config(
    page_title            = "Eco AI — Pakistan Waste Manager",
    page_icon             = "♻️",
    layout                = "wide",
    initial_sidebar_state = "expanded"
)

# ════════════════════════════════════════════════════════════
# CSS — Light Professional Theme + Mobile-First
# ════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

/* ── Variables ── */
:root {
    --green      : #166534;
    --green-mid  : #16a34a;
    --green-light: #22c55e;
    --green-bg   : #f0fdf4;
    --green-bdr  : #bbf7d0;
    --white      : #ffffff;
    --bg         : #f8fafc;
    --text-1     : #0f172a;
    --text-2     : #334155;
    --text-3     : #64748b;
    --text-4     : #94a3b8;
    --border     : #e2e8f0;
    --danger     : #dc2626;
    --danger-bg  : #fef2f2;
    --warn-bg    : #fffbeb;
    --warn-txt   : #92400e;
    --shadow-xs  : 0 1px 2px rgba(0,0,0,0.05);
    --shadow-sm  : 0 1px 6px rgba(0,0,0,0.07);
    --shadow-md  : 0 4px 16px rgba(0,0,0,0.09);
    --shadow-lg  : 0 8px 30px rgba(0,0,0,0.11);
    --r-sm       : 8px;
    --r-md       : 14px;
    --r-lg       : 20px;
    --r-xl       : 28px;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family : 'Inter', sans-serif !important;
    background  : var(--bg) !important;
    color       : var(--text-1) !important;
    -webkit-font-smoothing: antialiased;
}
h1,h2,h3,h4,h5 {
    font-family : 'Syne', sans-serif !important;
    color       : var(--text-1) !important;
    line-height : 1.2 !important;
}
p, li, div { color: var(--text-2); }
small, caption, .caption { color: var(--text-3) !important; }
strong, b { color: var(--text-1) !important; font-weight: 600 !important; }
a { color: var(--green-mid) !important; }
code {
    background    : var(--green-bg) !important;
    color         : var(--green) !important;
    padding       : 0.1rem 0.4rem !important;
    border-radius : 5px !important;
    font-size     : 0.85em !important;
}

/* ── Always-visible sidebar ── */
[data-testid="stSidebar"] {
    background    : var(--white) !important;
    border-right  : 1px solid var(--border) !important;
}
[data-testid="collapsedControl"] { display: none !important; }

/* ── Streamlit overrides ── */
.stButton > button {
    font-family   : 'Inter', sans-serif !important;
    font-weight   : 600 !important;
    border-radius : var(--r-sm) !important;
    font-size     : 0.88rem !important;
    transition    : all 0.15s !important;
}
.stButton > button[kind="primary"] {
    background : var(--green) !important;
    border     : none !important;
    color      : #ffffff !important;
}
.stButton > button[kind="primary"]:hover {
    background : #14532d !important;
}
.stButton > button[kind="secondary"] {
    background : var(--white) !important;
    border     : 1.5px solid var(--green) !important;
    color      : var(--green) !important;
}
.stButton > button[kind="secondary"]:hover {
    background : var(--green-bg) !important;
}
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea,
.stSelectbox > div > div {
    font-family   : 'Inter', sans-serif !important;
    font-size     : 0.9rem !important;
    color         : var(--text-1) !important;
    background    : var(--white) !important;
    border        : 1.5px solid var(--border) !important;
    border-radius : var(--r-sm) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color : var(--green-mid) !important;
    box-shadow   : 0 0 0 3px rgba(22,163,74,0.12) !important;
    outline      : none !important;
}
label, .stRadio label, .stCheckbox label {
    color       : var(--text-2) !important;
    font-weight : 500 !important;
    font-size   : 0.88rem !important;
}
.stTabs [data-baseweb="tab"] {
    font-family : 'Inter', sans-serif !important;
    font-weight : 600 !important;
    font-size   : 0.88rem !important;
    color       : var(--text-3) !important;
}
.stTabs [aria-selected="true"] {
    color            : var(--green) !important;
    border-bottom    : 2px solid var(--green) !important;
}
.stMetric {
    background    : var(--white) !important;
    border        : 1px solid var(--border) !important;
    border-radius : var(--r-sm) !important;
    padding       : 0.8rem !important;
    box-shadow    : var(--shadow-xs) !important;
}
.stMetric label { color: var(--text-3) !important; font-size:0.78rem !important; }
[data-testid="metric-value"] {
    color       : var(--green) !important;
    font-family : 'Syne', sans-serif !important;
    font-weight : 700 !important;
}
[data-testid="stExpander"] {
    background    : var(--white) !important;
    border        : 1px solid var(--border) !important;
    border-radius : var(--r-sm) !important;
}
.stAlert { border-radius: var(--r-sm) !important; }
#MainMenu, footer, header { visibility: hidden !important; }

/* ── Header banner ── */
.eco-header {
    background    : linear-gradient(135deg, #14532d 0%, #166534 45%, #16a34a 100%);
    border-radius : var(--r-lg);
    padding       : 1.8rem 2rem;
    margin-bottom : 1.2rem;
    position      : relative;
    overflow      : hidden;
}
.eco-header::after {
    content    : '♻';
    position   : absolute; right: 1.5rem; top: 50%;
    transform  : translateY(-50%);
    font-size  : 5rem; opacity: 0.08; line-height:1;
}
.eco-header h1 {
    font-size   : 1.8rem !important; margin: 0 !important;
    color       : #ffffff !important; letter-spacing: -0.3px;
}
.eco-header p { margin: 0.3rem 0 0; opacity: 0.88; font-size:0.88rem; color: #dcfce7 !important; }

/* ── Cards ── */
.card {
    background    : var(--white);
    border-radius : var(--r-md);
    padding       : 1.4rem;
    box-shadow    : var(--shadow-sm);
    border        : 1px solid var(--border);
    margin-bottom : 1rem;
}
.card-green  { border-left: 4px solid var(--green-mid); }
.card-danger { border-left: 4px solid var(--danger); background: var(--danger-bg); }
.card-warn   { border-left: 4px solid #f59e0b; background: var(--warn-bg); }

/* ── AI response box ── */
.ai-box {
    background    : var(--white);
    border-radius : var(--r-md);
    padding       : 1.6rem;
    box-shadow    : var(--shadow-sm);
    border-top    : 3px solid var(--green-mid);
    border        : 1px solid var(--border);
    border-top    : 3px solid var(--green-mid);
    line-height   : 1.85;
    font-size     : 0.93rem;
    color         : var(--text-2) !important;
    margin-bottom : 1rem;
}

/* ── Badges ── */
.badge { border-radius:20px; padding:0.2rem 0.8rem; font-size:0.79rem; font-weight:600; display:inline-block; }
.b-yes   { background:#dcfce7; color:#14532d; }
.b-no    { background:#fee2e2; color:#991b1b; }
.b-demo  { background:#fef3c7; color:#92400e; border:1px solid #fde68a; }
.b-info  { background:#eff6ff; color:#1d4ed8; }

/* ── Harm level colours ── */
.h-low  { color:#15803d; font-weight:600; }
.h-med  { color:#b45309; font-weight:600; }
.h-high { color:#c2410c; font-weight:600; }
.h-vhi  { color:#dc2626; font-weight:600; }

/* ── Input mode selector ── */
.mode-btn {
    background    : var(--white);
    border        : 1.5px solid var(--border);
    border-radius : var(--r-md);
    padding       : 1.1rem 0.8rem;
    text-align    : center;
    cursor        : pointer;
    transition    : all 0.18s;
}
.mode-btn.active { border-color: var(--green-mid); background: var(--green-bg); }
.mode-btn .icon  { font-size: 1.8rem; display:block; margin-bottom:0.4rem; }
.mode-btn .lbl   { font-weight:600; font-size:0.85rem; color:var(--text-1) !important; }

/* ── Voice box ── */
.voice-box {
    background    : var(--green-bg);
    border        : 2px dashed var(--green-mid);
    border-radius : var(--r-md);
    padding       : 1.5rem;
    text-align    : center;
    margin-bottom : 0.8rem;
}

/* ── Nearby card ── */
.nearby-card {
    background    : var(--white);
    border-left   : 3px solid var(--green-mid);
    border-radius : var(--r-sm);
    padding       : 0.85rem 1rem;
    margin-bottom : 0.5rem;
    box-shadow    : var(--shadow-xs);
}

/* ── Market table ── */
.mkt-row {
    display          : flex;
    justify-content  : space-between;
    align-items      : center;
    padding          : 0.5rem 0;
    border-bottom    : 1px solid var(--border);
    font-size        : 0.88rem;
}
.mkt-row:last-child { border-bottom:none; }
.mkt-price { color: var(--green) !important; font-weight:700; }

/* ── Chat bubbles ── */
.bubble-user { background:#dcfce7; border-radius:14px 14px 3px 14px; padding:0.65rem 1rem; margin-bottom:0.4rem; }
.bubble-ai   {
    background    : var(--white);
    border        : 1px solid var(--border);
    border-radius : 14px 14px 14px 3px;
    padding       : 0.65rem 1rem;
    margin-bottom : 0.4rem;
    box-shadow    : var(--shadow-xs);
}

/* ── Review box ── */
.review-box {
    background    : var(--white);
    border-radius : var(--r-md);
    border        : 1px solid var(--border);
    border-top    : 3px solid #f59e0b;
    padding       : 1.3rem;
    margin-bottom : 1rem;
    box-shadow    : var(--shadow-xs);
}
.review-done {
    background    : #dcfce7;
    border-radius : var(--r-sm);
    padding       : 0.9rem;
    text-align    : center;
    color         : #14532d !important;
    font-weight   : 600;
}

/* ── Demo grid card ── */
.demo-card {
    background    : var(--white);
    border        : 1.5px solid var(--border);
    border-radius : var(--r-md);
    padding       : 0.75rem;
    text-align    : center;
    transition    : all 0.18s;
    box-shadow    : var(--shadow-xs);
}
.demo-card:hover { border-color: var(--green-mid); transform:translateY(-2px); box-shadow:var(--shadow-md); }

/* ── Team card ── */
.team-card {
    background    : var(--white);
    border-radius : var(--r-lg);
    padding       : 1.6rem 1.2rem;
    box-shadow    : var(--shadow-sm);
    border        : 1px solid var(--border);
    border-top    : 4px solid var(--green-mid);
    text-align    : center;
    transition    : transform 0.2s, box-shadow 0.2s;
    height        : 100%;
}
.team-card:hover { transform:translateY(-4px); box-shadow:var(--shadow-lg); }
.t-avatar {
    width:72px; height:72px; border-radius:50%;
    background:linear-gradient(135deg,#14532d,#22c55e);
    display:flex; align-items:center; justify-content:center;
    font-size:1.7rem; margin:0 auto 0.9rem;
    color:white; font-family:'Syne',sans-serif; font-weight:800;
    box-shadow: 0 4px 12px rgba(22,163,74,0.35);
}
.t-name { font-family:'Syne',sans-serif; font-weight:700; font-size:0.95rem; color:var(--text-1) !important; }
.t-role { color:var(--green) !important; font-weight:600; font-size:0.8rem; margin:0.2rem 0; }
.t-acad { color:var(--text-3) !important; font-size:0.76rem; font-style:italic; margin-bottom:0.7rem; }
.t-links { display:flex; justify-content:center; gap:0.4rem; flex-wrap:wrap; margin-top:0.6rem; }
.t-link  {
    display:inline-flex; align-items:center; gap:0.3rem;
    background:var(--green-bg); color:var(--green) !important;
    border-radius:20px; padding:0.25rem 0.75rem;
    font-size:0.76rem; font-weight:600; text-decoration:none;
    border:1px solid var(--green-bdr); transition:background 0.15s;
}
.t-link:hover { background:var(--green-bdr); }
.t-ph {
    background:var(--bg); border-radius:var(--r-lg);
    border:2px dashed var(--border); padding:1.6rem 1rem;
    text-align:center; color:var(--text-4) !important; height:100%;
}

/* ── Nav button ── */
.nav-btn {
    display:inline-block; background:var(--green); color:#ffffff !important;
    border-radius:var(--r-sm); padding:0.45rem 0.9rem; font-weight:600;
    font-size:0.8rem; text-decoration:none; margin-top:0.4rem;
    transition:background 0.15s; white-space:nowrap;
}
.nav-btn:hover { background:#14532d; }

/* ── User bar ── */
.user-bar {
    background    : var(--green-bg);
    border        : 1px solid var(--green-bdr);
    border-radius : var(--r-sm);
    padding       : 0.5rem 1rem;
    margin-bottom : 1rem;
    display       : flex;
    align-items   : center;
    gap           : 0.7rem;
    flex-wrap     : wrap;
    font-size     : 0.83rem;
}
.user-bar span { color: var(--text-2) !important; }
.user-bar .sep { color: var(--border) !important; }

/* ══════════════════════════════════════════════════════════
   MOBILE — max-width 768px
══════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
    /* Header */
    .eco-header { padding:1.2rem 1rem; border-radius:var(--r-md); }
    .eco-header h1 { font-size:1.25rem !important; }
    .eco-header::after { display:none; }

    /* Cards & boxes */
    .card, .ai-box, .review-box { padding:1rem; }
    .ai-box { font-size:0.88rem; }

    /* Team grid: 2 columns on mobile */
    .team-card { padding:1.1rem 0.8rem; }
    .t-avatar  { width:58px; height:58px; font-size:1.4rem; }

    /* Metrics stack better */
    [data-testid="column"] { padding:0.15rem !important; }

    /* Tabs: compact text */
    .stTabs [data-baseweb="tab"] { font-size:0.78rem !important; padding:0.4rem 0.5rem !important; }

    /* Market table */
    .mkt-row { font-size:0.82rem; }

    /* Hide sidebar toggle arrow (already forced open) */
    [data-testid="collapsedControl"] { display:none !important; }
}

/* ══════════════════════════════════════════════════════════
   MOBILE — max-width 480px (small phones)
══════════════════════════════════════════════════════════ */
@media (max-width: 480px) {
    .eco-header h1 { font-size:1.05rem !important; }
    .eco-header p  { font-size:0.78rem; }
    .stButton > button { font-size:0.8rem !important; padding:0.4rem 0.6rem !important; }
    .badge { font-size:0.72rem !important; padding:0.15rem 0.6rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════
DEMO_IMAGES = [
    {"label":"Plastic Bottle","emoji":"🧴","category":"plastic",
     "url":"https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&q=80","hint":"Recyclable · Low"},
    {"label":"Cardboard Box","emoji":"📦","category":"cardboard",
     "url":"https://images.unsplash.com/photo-1607166452427-7e4477079cb9?w=400&q=80","hint":"Recyclable · Low"},
    {"label":"Glass Bottle","emoji":"🍾","category":"glass",
     "url":"https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=400&q=80","hint":"Recyclable · Med"},
    {"label":"Rubber Tyre","emoji":"⚫","category":"rubber",
     "url":"https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400&q=80","hint":"Recyclable · Med"},
    {"label":"Organic Waste","emoji":"🍌","category":"organic",
     "url":"https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&q=80","hint":"Compost · Low"},
]

TEAM = [
    {"name":"Suhani","initials":"S","role":"Team Leader",
     "academic":"DAE Software Student",
     "linkedin":"https://www.linkedin.com/in/suhan-i/",
     "github":"https://github.com/SUHAN-I"},
    {"name":"Muhammad Haroon ul Hasnain","initials":"H","role":"Team Member",
     "academic":"MPhil BA & DA",
     "linkedin":"https://www.linkedin.com/in/muhammad-haroon-ul-hasnain",
     "github":"https://github.com/hasnain1669"},
    None, None, None,
]

MARKET = {
    "Plastic"  :("PKR 60–140/kg",   "پلاسٹک"),
    "Glass"    :("PKR 15–40/kg",    "شیشہ"),
    "Metal"    :("PKR 80–350/kg",   "دھات"),
    "Paper"    :("PKR 20–55/kg",    "کاغذ"),
    "Cardboard":("PKR 25–60/kg",    "گتہ"),
    "E-Waste"  :("PKR 200–800/kg",  "الیکٹرانک"),
    "Textile"  :("PKR 30–120/kg",   "کپڑے"),
    "Rubber"   :("PKR 40–90/kg",    "ربڑ"),
    "Organic"  :("Compost/Biogas",  "نامیاتی"),
    "Hazardous":("Special disposal","خطرناک"),
}

VALID_WASTE = {"plastic","glass","metal","paper","cardboard",
               "e-waste","textile","rubber","organic","hazardous","trash"}

HARM_MAP = {
    "low"      :('<span class="h-low">🟢 Low</span>',       '<span class="h-low">🟢 کم</span>'),
    "medium"   :('<span class="h-med">🟡 Medium</span>',    '<span class="h-med">🟡 درمیانہ</span>'),
    "high"     :('<span class="h-high">🟠 High</span>',     '<span class="h-high">🟠 زیادہ</span>'),
    "very high":('<span class="h-vhi">🔴 Very High</span>', '<span class="h-vhi">🔴 بہت زیادہ</span>'),
}

# ════════════════════════════════════════════════════════════
# BILINGUAL TEXT
# ════════════════════════════════════════════════════════════
UI = {
    "title"     :{"en":"🌿 Eco AI — Pakistan Waste Manager","ur":"🌿 ایکو اے آئی — پاکستان"},
    "subtitle"  :{"en":"Scan waste · Recycling guide · PKR market rates",
                  "ur":"کچرا اسکین · ری سائیکلنگ گائیڈ · مارکیٹ ریٹ"},
    "tab_scan"  :{"en":"🔍 Scan","ur":"🔍 اسکین"},
    "tab_demo"  :{"en":"🎯 Judge Demo","ur":"🎯 جج ڈیمو"},
    "tab_team"  :{"en":"👥 Team","ur":"👥 ٹیم"},
    "inp_q"     :{"en":"How would you like to describe the waste?","ur":"فضلے کو کیسے بیان کریں؟"},
    "opt_img"   :{"en":"📷 Image","ur":"📷 تصویر"},
    "opt_txt"   :{"en":"✏️ Text","ur":"✏️ متن"},
    "opt_voice" :{"en":"🎤 Voice","ur":"🎤 آواز"},
    "cam_lbl"   :{"en":"📷 Camera","ur":"📷 کیمرہ"},
    "upl_lbl"   :{"en":"📁 Upload","ur":"📁 اپلوڈ"},
    "txt_ph"    :{"en":"Describe the waste (e.g. 'crushed plastic bottle')…",
                  "ur":"فضلے کو بیان کریں (مثلاً 'پلاسٹک بوتل')…"},
    "analyse"   :{"en":"🔍 Analyse","ur":"🔍 تجزیہ"},
    "not_waste" :{"en":"🚫 Not Waste Detected","ur":"🚫 کچرہ نہیں ملا"},
    "not_waste_m":{"en":"This image doesn't contain identifiable waste. Please upload a clear waste photo.",
                   "ur":"اس تصویر میں کچرہ نہیں ملا۔ واضح تصویر اپلوڈ کریں۔"},
    "ai_guide"  :{"en":"📝 AI Recycling & Business Guide","ur":"📝 اے آئی ری سائیکلنگ گائیڈ"},
    "fup_ph"    :{"en":"💬 Ask a follow-up question…","ur":"💬 مزید سوال پوچھیں…"},
    "ask"       :{"en":"Ask","ur":"پوچھیں"},
    "speak_btn" :{"en":"🔊 Listen to AI Response","ur":"🔊 جواب سنیں"},
    "yes"       :{"en":"YES ✅","ur":"ہاں ✅"},
    "no"        :{"en":"NO ❌","ur":"نہیں ❌"},
    "cat"       :{"en":"Category","ur":"کیٹیگری"},
    "recyc"     :{"en":"Recyclable","ur":"قابل ری سائیکل"},
    "harm"      :{"en":"Harm","ur":"نقصان"},
    "conf"      :{"en":"Confidence","ur":"اعتماد"},
    "nearby"    :{"en":"📍 Nearby","ur":"📍 قریبی"},
    "history"   :{"en":"📋 History","ur":"📋 تاریخ"},
    "market"    :{"en":"💰 Market","ur":"💰 مارکیٹ"},
    "stats"     :{"en":"📊 Stats","ur":"📊 اعداد"},
    "chat_hist" :{"en":"💬 Chat History","ur":"💬 گفتگو"},
    "saved"     :{"en":"✅ Scan saved!","ur":"✅ اسکین محفوظ!"},
    "city"      :{"en":"City","ur":"شہر"},
    "lat"       :{"en":"Latitude","ur":"عرض بلد"},
    "lng"       :{"en":"Longitude","ur":"طول بلد"},
    "sources"   :{"en":"📚 Knowledge sources","ur":"📚 ماخذ"},
    "no_scans"  :{"en":"No scans yet.","ur":"کوئی اسکین نہیں۔"},
    "no_nearby" :{"en":"No nearby scans found.","ur":"قریبی اسکین نہیں ملا۔"},
    "no_chat"   :{"en":"No chat history yet.","ur":"کوئی گفتگو نہیں۔"},
    "rv_title"  :{"en":"⭐ Rate This Classification","ur":"⭐ اس تجزیے کو ریٹ کریں"},
    "rv_q"      :{"en":"Was this correctly identified?","ur":"کیا درست پہچانا گیا؟"},
    "rv_stars"  :{"en":"Your Rating","ur":"ریٹنگ"},
    "rv_fb"     :{"en":"Feedback (optional)","ur":"رائے (اختیاری)"},
    "rv_cor"    :{"en":"Correct waste type","ur":"درست قسم"},
    "rv_sub"    :{"en":"Submit Review","ur":"جائزہ جمع کریں"},
    "rv_thanks" :{"en":"✅ Thank you!","ur":"✅ شکریہ!"},
    "rv_saved"  :{"en":"Your feedback improves our AI.","ur":"آپ کی رائے AI کو بہتر بناتی ہے۔"},
    "show_demo" :{"en":"👁️ Show Demo Images","ur":"👁️ ڈیمو تصاویر دکھائیں"},
    "hide_demo" :{"en":"🙈 Hide","ur":"🙈 چھپائیں"},
    "demo_try"  :{"en":"Click any image to test the AI:","ur":"AI آزمانے کے لیے تصویر کلک کریں:"},
    "team_title":{"en":"👥 Meet Our Team","ur":"👥 ہماری ٹیم"},
    "team_sub"  :{"en":"Building Pakistan's circular economy with AI",
                  "ur":"اے آئی سے پاکستان کی سرکلر اکانومی"},
    "coming"    :{"en":"Coming Soon","ur":"جلد آ رہا ہے"},
    "voice_hint":{"en":"Speak now — describe the waste or ask a question",
                  "ur":"اب بولیں — فضلے کو بیان کریں یا سوال پوچھیں"},
}

def t(k, lang): return UI.get(k,{}).get("ur" if lang=="urdu" else "en", k)
def tk(k): return f"show_{k}"
def harm_html(level, lang):
    key = level.lower().replace(" ","")
    idx = 1 if lang=="urdu" else 0
    return HARM_MAP.get(key, HARM_MAP["medium"])[idx]
def gmaps(lat,lng): return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
def osm(lat,lng):   return f"https://www.openstreetmap.org/directions?to={lat},{lng}"


# ════════════════════════════════════════════════════════════
# CACHED LOADERS
# ════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner="🦙 Loading Vision AI…")
def get_vclient():
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
        gsheet_id=st.secrets["GSHEET_ID"], gsheet_credentials=creds,
        qdrant_url=st.secrets["QDRANT_URL"], qdrant_api_key=st.secrets["QDRANT_API_KEY"],
        cloudinary_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        cloudinary_key=st.secrets["CLOUDINARY_API_KEY"],
        cloudinary_secret=st.secrets["CLOUDINARY_API_SECRET"]
    )

@st.cache_resource(show_spinner="🎤 Loading Voice AI…")
def get_whisper():
    try:
        from voice import load_whisper_model
        return load_whisper_model()
    except: return None


# ════════════════════════════════════════════════════════════
# STATE INIT
# ════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "show_nearby":False,"show_history":False,"show_market":False,
        "show_stats":False,"show_demo_images":False,"show_chat_hist":False,
        "review_submitted":False,"last_vision":None,"rag_result":None,
        "input_mode":"image","session_id":str(uuid.uuid4())[:8],
        "save_preference":None,"current_user":None,"show_id_popup":False,
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def is_valid_waste(v):
    cat = v.get("label","").lower()
    if cat not in VALID_WASTE: return False
    if cat=="trash" and v.get("confidence","low")=="low" and "no waste" in v.get("waste_type","").lower(): return False
    return True

def save_chat(db, role, message, waste_type=""):
    user = st.session_state.get("current_user")
    if not user or user.get("user_id")=="GUEST": return
    try:
        from user_manager import save_chat_message
        save_chat_message(db, user, role, message, waste_type,
                          st.session_state.get("session_id",""))
    except: pass


# ════════════════════════════════════════════════════════════
# USER MODAL
# ════════════════════════════════════════════════════════════
def render_user_modal(db):
    if st.session_state.get("current_user"): return

    overlay = """<div style="position:fixed;top:0;left:0;right:0;bottom:0;
        background:rgba(15,23,42,0.55);z-index:9990;backdrop-filter:blur(3px)"></div>"""

    # Step 1 — save preference
    if st.session_state["save_preference"] is None:
        st.markdown(overlay, unsafe_allow_html=True)
        st.markdown("""<div style="background:white;border-radius:24px;padding:2rem 2rem 1.6rem;
            max-width:420px;margin:3rem auto;position:relative;z-index:9999;
            box-shadow:0 24px 64px rgba(0,0,0,0.22);text-align:center">
            <div style="font-size:3rem;margin-bottom:0.5rem">♻️</div>
            <h3 style="font-family:Syne,sans-serif;color:#0f172a;margin:0 0 0.4rem">Welcome to Eco AI!</h3>
            <p style="color:#64748b;font-size:0.88rem;margin-bottom:1.5rem">
                Would you like to save your scans and chat history for future visits?
            </p>
        </div>""", unsafe_allow_html=True)
        c1,c2,c3 = st.columns([1,3,1])
        with c2:
            if st.button("✅ Yes — Save My Data", type="primary", use_container_width=True, key="sp_yes"):
                st.session_state["save_preference"] = True; st.rerun()
            st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
            if st.button("⏭️ Continue as Guest", type="secondary", use_container_width=True, key="sp_no"):
                st.session_state["save_preference"] = False
                st.session_state["current_user"] = {"user_id":"GUEST","name":"Guest","city":"—","is_new":False}
                st.rerun()
        return

    # Step 2 — new / returning
    if st.session_state["save_preference"] and not st.session_state.get("current_user"):
        st.markdown(overlay, unsafe_allow_html=True)
        st.markdown("""<div style="background:white;border-radius:24px;padding:1.8rem 2rem 1.5rem;
            max-width:460px;margin:2rem auto;position:relative;z-index:9999;
            box-shadow:0 24px 64px rgba(0,0,0,0.22)">
            <h3 style="font-family:Syne,sans-serif;color:#0f172a;text-align:center;margin:0 0 1rem">
                👤 Who are you?
            </h3>
        </div>""", unsafe_allow_html=True)

        c1,c2,c3 = st.columns([1,4,1])
        with c2:
            is_new = st.radio("Type",["new","returning"],
                format_func=lambda x:"🌱 New User" if x=="new" else "👋 Returning User",
                horizontal=True, key="u_type")
            st.markdown("<hr style='margin:0.7rem 0;border-color:#f1f5f9'>", unsafe_allow_html=True)

            if is_new == "new":
                nm = st.text_input("Your Name *", placeholder="e.g. Ahmed, Sara…", key="new_nm")
                ct = st.text_input("Your City *", placeholder="e.g. Lahore, Karachi…", key="new_ct")
                if st.button("🚀 Register & Continue", type="primary", use_container_width=True, key="reg_btn"):
                    if nm.strip() and ct.strip():
                        with st.spinner("Creating account…"):
                            from user_manager import register_new_user
                            user = register_new_user(db, nm.strip(), ct.strip())
                        if user:
                            st.session_state["current_user"] = user
                            st.session_state["show_id_popup"] = True
                            st.rerun()
                        else: st.error("Registration failed. Try again.")
                    else: st.warning("Please fill in name and city.")
            else:
                rn = st.text_input("Your Name *", placeholder="Your name", key="ret_nm")
                ri = st.text_input("Your Unique ID", placeholder="e.g. ECO-LEAF-293 (leave blank to find by name)", key="ret_id")
                if st.button("🔑 Login", type="primary", use_container_width=True, key="login_btn"):
                    if rn.strip():
                        with st.spinner("Finding account…"):
                            from user_manager import find_user
                            user = find_user(db, user_id=ri.strip() or None, name=rn.strip())
                        if user:
                            st.session_state["current_user"] = user; st.rerun()
                        else: st.error(f"User '{rn}' not found. Check your ID or register.")
                    else: st.warning("Please enter your name.")
                with st.expander("🤔 Forgot your ID?"):
                    st.markdown("Just enter your **name** and leave the ID blank. We'll find you by name.\nIf that fails, register as a new user.")

            st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
            if st.button("⏭️ Skip for now", key="skip_m", use_container_width=True):
                st.session_state["save_preference"] = False
                st.session_state["current_user"] = {"user_id":"GUEST","name":"Guest","city":"—","is_new":False}
                st.rerun()


def render_id_popup():
    if not st.session_state.get("show_id_popup"): return
    user = st.session_state.get("current_user",{})
    uid  = user.get("user_id","")
    name = user.get("name","")
    st.markdown("""<div style="position:fixed;top:0;left:0;right:0;bottom:0;
        background:rgba(15,23,42,0.6);z-index:9990;backdrop-filter:blur(4px)"></div>""",
        unsafe_allow_html=True)
    st.markdown(f"""<div style="background:white;border-radius:24px;padding:2rem 2rem 1.6rem;
        max-width:400px;margin:3rem auto;position:relative;z-index:9999;
        box-shadow:0 24px 64px rgba(0,0,0,0.25);text-align:center">
        <div style="font-size:2.5rem;margin-bottom:0.5rem">🎉</div>
        <h3 style="font-family:Syne,sans-serif;color:#0f172a;margin:0 0 0.3rem">Welcome, {name}!</h3>
        <p style="color:#64748b;font-size:0.87rem;margin-bottom:1rem">Your account is ready. Save your unique ID:</p>
        <div style="background:linear-gradient(135deg,#14532d,#22c55e);border-radius:14px;
                    padding:1rem 1.5rem;margin:0.8rem 0 1rem">
            <div style="color:rgba(255,255,255,0.7);font-size:0.7rem;text-transform:uppercase;letter-spacing:1px">
                Your Unique ID</div>
            <div style="color:white;font-family:Syne,sans-serif;font-size:1.55rem;
                        font-weight:800;letter-spacing:2px;margin-top:0.2rem">{uid}</div>
        </div>
        <div style="background:#fffbeb;border-radius:10px;padding:0.75rem 1rem;
                    color:#92400e;font-size:0.83rem;text-align:left">
            📝 <strong>Remember this ID!</strong> You'll need it to access your
            conversation history in future visits.
        </div>
    </div>""", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        if st.button("✅ Got It — Let's Start!", type="primary", use_container_width=True, key="close_popup"):
            st.session_state["show_id_popup"] = False; st.rerun()


def render_user_bar(lang):
    user = st.session_state.get("current_user")
    if not user or user.get("user_id")=="GUEST": return
    st.markdown(f"""<div class="user-bar">
        <span>👤 <strong style="color:#0f172a">{user.get('name','')}</strong></span>
        <span class="sep">|</span>
        <span>🆔 <code>{user.get('user_id','')}</code></span>
        <span class="sep">|</span>
        <span>📍 {user.get('city','')}</span>
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# RESULT CARD
# ════════════════════════════════════════════════════════════
def render_result_card(v, lang):
    recyclable = v.get("recyclable", False)
    card_cls   = "card card-green" if recyclable else "card card-danger"
    badge_cls  = "badge b-yes" if recyclable else "badge b-no"
    badge_txt  = t("yes",lang) if recyclable else t("no",lang)
    harm       = harm_html(v.get("harmful_level","medium"), lang)
    st.markdown(f"""<div class="{card_cls}">
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.1rem">
            <span style="font-size:2.5rem;line-height:1">{v.get('emoji','♻️')}</span>
            <div>
                <div style="font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;
                            color:#0f172a;line-height:1.15">
                    {v.get('waste_type','Unknown').title()}</div>
                <div style="color:#64748b;font-size:0.88rem;margin-top:0.1rem">
                    {v.get('urdu_label','نامعلوم')}</div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.7rem;margin-bottom:0.85rem">
            <div><div style="font-size:0.67rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.7px;
                        margin-bottom:0.25rem">{t('cat',lang)}</div>
                <strong style="color:#0f172a;font-size:0.87rem">{v.get('label_en','—')}</strong></div>
            <div><div style="font-size:0.67rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.7px;
                        margin-bottom:0.25rem">{t('recyc',lang)}</div>
                <span class="{badge_cls}">{badge_txt}</span></div>
            <div><div style="font-size:0.67rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.7px;
                        margin-bottom:0.25rem">{t('harm',lang)}</div>
                {harm}</div>
            <div><div style="font-size:0.67rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.7px;
                        margin-bottom:0.25rem">{t('conf',lang)}</div>
                <strong style="color:#0f172a;font-size:0.87rem">{v.get('confidence','—').upper()}</strong></div>
        </div>
        <div style="font-size:0.83rem;color:#64748b;font-style:italic;
                    border-top:1px solid #f1f5f9;padding-top:0.6rem">
            💬 {v.get('reasoning','')}</div>
    </div>""", unsafe_allow_html=True)
    if v.get("is_demo"):
        st.markdown('<span class="badge b-demo">⚠️ Demo Mode</span>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# REVIEW
# ════════════════════════════════════════════════════════════
def render_review(db, v, lang):
    st.markdown("---")
    st.markdown(f"""<div class="review-box">
        <div style="font-family:Syne,sans-serif;font-weight:700;font-size:0.97rem;
                    color:#0f172a;margin-bottom:1rem">{t('rv_title',lang)}</div>
    </div>""", unsafe_allow_html=True)
    if st.session_state.get("review_submitted"):
        st.markdown(f"""<div class="review-done">
            {t('rv_thanks',lang)}<br>
            <small style="font-weight:400;color:#166534">{t('rv_saved',lang)}</small>
        </div>""", unsafe_allow_html=True)
        if st.button("✏️ Edit", key="rv_edit"):
            st.session_state["review_submitted"] = False; st.rerun()
        return
    rc1,rc2 = st.columns([1,2])
    with rc1:
        st.markdown(f"**{t('rv_stars',lang)}**")
        stars = st.select_slider("rv_sl",[1,2,3,4,5],5,
                    format_func=lambda x:"⭐"*x, label_visibility="collapsed", key="rv_s_w")
        st.markdown(f"{'⭐'*stars}{'☆'*(5-stars)}")
    with rc2:
        st.markdown(f"**{t('rv_q',lang)}**")
        correct = st.radio("rv_c_r",["yes","no"],
            format_func=lambda x:("✅ Yes" if lang=="english" else "✅ ہاں") if x=="yes"
                                 else("❌ No" if lang=="english" else "❌ نہیں"),
            horizontal=True, index=0, label_visibility="collapsed", key="rv_c_w")
    correction = ""
    if correct == "no":
        correction = st.text_input(t("rv_cor",lang), placeholder="e.g. metal can", key="rv_cor_i")
    feedback = st.text_area(t("rv_fb",lang), placeholder=t("rv_fb",lang),
                            height=75, label_visibility="collapsed", key="rv_fb_w")
    if st.button(t("rv_sub",lang), type="primary", key="rv_sub_btn"):
        try:
            sheet = db.get("sheet")
            if sheet:
                try: ws = sheet.worksheet("reviews")
                except:
                    ws = sheet.add_worksheet(title="reviews",rows=1000,cols=10)
                    ws.append_row(["timestamp","user_id","waste_type","stars","correct","correction","feedback","language"])
                user = st.session_state.get("current_user",{})
                ws.append_row([datetime.now().isoformat(), user.get("user_id","GUEST"),
                               v.get("waste_type",""), stars, correct, correction, feedback, lang])
        except: pass
        st.session_state["review_submitted"] = True; st.rerun()


# ════════════════════════════════════════════════════════════
# EXPLORE MORE SECTIONS
# ════════════════════════════════════════════════════════════
def section_nearby(db, lat, lng, lang):
    st.markdown(f"#### {t('nearby',lang)}")
    with st.spinner("Searching…"):
        from database import get_nearby_scans
        scans = get_nearby_scans(db, lat, lng, limit=10)
    if not scans: st.info(t("no_nearby",lang)); return
    st.success(f"Found **{len(scans)}** nearby scans")
    for s in scans:
        emoji = "♻️" if s.get("recyclable") else "🗑️"
        s_lat = s.get("latitude",0.0); s_lng = s.get("longitude",0.0)
        c1,c2,c3 = st.columns([3,3,1])
        with c1:
            st.markdown(f"""<div class="nearby-card">
                <strong style="color:#0f172a">{emoji} {s.get('waste_type','?').title()}</strong><br>
                <small style="color:#64748b">📍 {s.get('address','?')}</small>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"`{s.get('category','?')}` · {s.get('timestamp','')[:10]}")
            st.markdown(f'<a href="{gmaps(s_lat,s_lng)}" target="_blank" class="nav-btn">🗺️ Google Maps</a>',
                        unsafe_allow_html=True)
            st.markdown(f'<a href="{osm(s_lat,s_lng)}" target="_blank" class="nav-btn" style="background:#2563eb;margin-left:4px">🗺️ OSM</a>',
                        unsafe_allow_html=True)
        with c3:
            if s.get("image_url"): st.image(s["image_url"], width=65)


def section_history(db, lang):
    st.markdown(f"#### {t('history',lang)}")
    from database import get_recent_scans
    rows = get_recent_scans(db, limit=20)
    if not rows: st.info(t("no_scans",lang)); return
    for row in rows:
        recyc = row.get("recyclable","").lower()=="true"
        st.markdown(f"{'♻️' if recyc else '🗑️'} **{row.get('waste_type','—').title()}** "
                    f"· `{row.get('category','—')}` · {row.get('city','—')} "
                    f"· <span style='color:#94a3b8;font-size:0.8rem'>{row.get('timestamp','—')[:10]}</span>",
                    unsafe_allow_html=True)


def section_market(lang):
    st.markdown(f"#### {t('market',lang)}")
    st.caption("Misri Shah Lahore & Karachi scrap markets")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    for cat,(rate,urdu) in MARKET.items():
        label = urdu if lang=="urdu" else cat
        st.markdown(f"""<div class="mkt-row">
            <span style="color:#334155">{label}</span>
            <span class="mkt-price">{rate}</span>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.caption("⚠️ Approximate — verify with local dealers.")


def section_stats(db, lang):
    st.markdown(f"#### {t('stats',lang)}")
    try:
        from database import get_recent_scans
        rows = get_recent_scans(db, limit=200)
        if not rows: st.info(t("no_scans",lang)); return
        cats = {}; rc = 0
        for row in rows:
            cats[row.get("category","unknown")] = cats.get(row.get("category","unknown"),0)+1
            if row.get("recyclable","").lower()=="true": rc+=1
        total = len(rows)
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Total",total); m2.metric("Recyclable",rc)
        m3.metric("Non-Recyclable",total-rc); m4.metric("Categories",len(cats))
        if cats:
            import pandas as pd
            df = pd.DataFrame(list(cats.items()),columns=["Category","Count"]).sort_values("Count",ascending=False)
            st.bar_chart(df.set_index("Category"))
    except Exception as e: st.error(f"Stats error: {e}")


def section_chat_history(db, lang):
    st.markdown(f"#### {t('chat_hist',lang)}")
    user = st.session_state.get("current_user")
    if not user or user.get("user_id")=="GUEST":
        st.info("Log in to view your chat history."); return
    try:
        from user_manager import get_user_chat_history
        msgs = get_user_chat_history(db, user["user_id"], limit=30)
        if not msgs: st.info(t("no_chat",lang)); return
        for m in msgs:
            role = m.get("role","user"); msg = m.get("message",""); ts = m.get("timestamp","")[:16]
            cls  = "bubble-user" if role=="user" else "bubble-ai"
            icon = "👤" if role=="user" else "🤖"
            st.markdown(f"""<div class="{cls}">
                <strong style="color:#0f172a">{icon} {role.title()}</strong>
                <span style="color:#94a3b8;font-size:0.75rem;margin-left:0.5rem">{ts}</span><br>
                <span style="color:#334155">{msg}</span>
            </div>""", unsafe_allow_html=True)
    except Exception as e: st.error(f"Chat history error: {e}")


# ════════════════════════════════════════════════════════════
# ANALYSIS RUNNER
# ════════════════════════════════════════════════════════════
def run_analysis(lang, city, lat, lng, db, vclient, components,
                 image_bytes=None, text_input=None):

    with st.spinner("🦙 Analysing…"):
        from vision import classify_waste
        if image_bytes:
            v = classify_waste(vclient, image_bytes)
        else:
            v = {"waste_type":text_input,"label":"trash","label_en":"Unknown Waste",
                 "urdu_label":"نامعلوم","recyclable":False,"harmful_level":"medium",
                 "confidence":"medium","emoji":"🗑️",
                 "market_search":f"{text_input} scrap rate PKR Pakistan",
                 "is_demo":False,"reasoning":"Classified from text description."}

    if image_bytes and not is_valid_waste(v):
        st.markdown(f"""<div class="card card-danger">
            <div style="display:flex;align-items:center;gap:1rem">
                <span style="font-size:2.5rem">🚫</span>
                <div>
                    <div style="font-family:Syne,sans-serif;font-weight:800;font-size:1.2rem;color:#dc2626">
                        {t('not_waste',lang)}</div>
                    <div style="color:#64748b;margin-top:0.3rem">{t('not_waste_m',lang)}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
        st.session_state["last_vision"] = None; return

    st.session_state.update({"last_vision":v,"rag_result":None,"review_submitted":False})

    # Save scan + increment count
    if db and image_bytes:
        try:
            from database import save_scan
            save_scan(db=db, vision_result=v, image_bytes=image_bytes,
                      latitude=lat, longitude=lng,
                      address=f"{city}, Pakistan", city=city, language=lang)
            st.toast(t("saved",lang), icon="✅")
            user = st.session_state.get("current_user")
            if user and user.get("user_id")!="GUEST":
                from user_manager import increment_scan_count
                increment_scan_count(db, user["user_id"])
        except Exception as e: st.toast(f"DB: {e}", icon="⚠️")

    save_chat(db,"user", text_input or "Image uploaded", v.get("waste_type",""))

    # Result card
    st.markdown("---")
    render_result_card(v, lang)

    # RAG guide
    with st.spinner("🤖 Generating guide…"):
        from rag_engine import run_rag_pipeline
        rag = run_rag_pipeline(components=components, vision_result=v, language=lang)
    st.session_state["rag_result"] = rag

    st.markdown(f"### {t('ai_guide',lang)}")
    st.markdown(f"""<div class="ai-box">
        {rag['answer'].replace(chr(10),'<br>')}
    </div>""", unsafe_allow_html=True)

    if rag.get("is_demo"):
        st.markdown('<span class="badge b-demo">⚠️ Demo Mode</span>', unsafe_allow_html=True)
    if rag.get("sources_used"):
        with st.expander(t("sources",lang)):
            for src in rag["sources_used"]: st.markdown(f"- `{src}`")
            st.caption(f"Chunks: {rag.get('chunks_used',0)}")

    save_chat(db,"assistant", rag["answer"][:800], v.get("waste_type",""))

    # TTS button
    try:
        from voice import speak, render_tts
        if st.button(t("speak_btn",lang), key="tts_btn"):
            with st.spinner("🔊 Generating audio…"):
                result = speak(rag["answer"][:450], lang)
            render_tts(st, result)
    except: pass

    # Review (always visible)
    render_review(db, v, lang)

    # Follow-up
    st.markdown("---")
    fc1,fc2 = st.columns([5,1])
    with fc1:
        fup = st.text_input(t("fup_ph",lang), key="fup_i",
                            label_visibility="collapsed", placeholder=t("fup_ph",lang))
    with fc2:
        ask = st.button(t("ask",lang), use_container_width=True, key="fup_btn")

    if ask and fup.strip():
        save_chat(db,"user", fup, v.get("waste_type",""))
        with st.spinner("🤖 Answering…"):
            from rag_engine import run_rag_pipeline
            fr = run_rag_pipeline(components=components, vision_result=v,
                                  user_question=fup, language=lang)
        st.markdown(f"""<div class="ai-box" style="border-top-color:#16a34a">
            <strong style="color:#0f172a">Q: {fup}</strong><br><br>
            {fr['answer'].replace(chr(10),'<br>')}
        </div>""", unsafe_allow_html=True)
        save_chat(db,"assistant", fr["answer"][:800], v.get("waste_type",""))

    # Explore more toggles
    st.markdown("---")
    st.markdown("### 🔽 " + ("Explore More" if lang=="english" else "مزید دیکھیں"))
    toggle_specs = [
        ("nearby",    t("nearby",    lang)),
        ("history",   t("history",   lang)),
        ("market",    t("market",    lang)),
        ("stats",     t("stats",     lang)),
        ("chat_hist", t("chat_hist", lang)),
    ]
    cols = st.columns(len(toggle_specs))
    for col,(key,label) in zip(cols, toggle_specs):
        with col:
            active = st.session_state.get(tk(key),False)
            if st.button(label, use_container_width=True, key=f"tb_{key}",
                         type="primary" if active else "secondary"):
                st.session_state[tk(key)] = not active; st.rerun()

    if st.session_state.get(tk("nearby")):    section_nearby(db,lat,lng,lang)
    if st.session_state.get(tk("history")):   section_history(db,lang)
    if st.session_state.get(tk("market")):    section_market(lang)
    if st.session_state.get(tk("stats")):     section_stats(db,lang)
    if st.session_state.get(tk("chat_hist")): section_chat_history(db,lang)


# ════════════════════════════════════════════════════════════
# TAB: SCAN
# ════════════════════════════════════════════════════════════
def render_scan_tab(lang, city, lat, lng, vclient, components, db):
    # Input mode selector
    st.markdown(f"**{t('inp_q',lang)}**")
    m1,m2,m3 = st.columns(3)
    for col,mode,lbl,icon in [
        (m1,"image",t("opt_img",lang),"📷"),
        (m2,"text", t("opt_txt",lang),"✏️"),
        (m3,"voice",t("opt_voice",lang),"🎤"),
    ]:
        with col:
            active = st.session_state["input_mode"]==mode
            btype  = "primary" if active else "secondary"
            if st.button(f"{icon} {lbl.split()[-1]}", use_container_width=True,
                         type=btype, key=f"mode_{mode}"):
                st.session_state["input_mode"] = mode; st.rerun()

    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
    mode = st.session_state["input_mode"]

    # ── IMAGE ──────────────────────────────────────────────────
    if mode == "image":
        tab1,tab2 = st.tabs([t("cam_lbl",lang), t("upl_lbl",lang)])
        img_bytes = None
        with tab1:
            cam = st.camera_input(t("cam_lbl",lang), label_visibility="collapsed")
            if cam: img_bytes = cam.getvalue()
        with tab2:
            upl = st.file_uploader(t("upl_lbl",lang), type=["jpg","jpeg","png","webp"],
                                   label_visibility="collapsed")
            if upl:
                img_bytes = upl.getvalue()
                st.image(img_bytes, width=280)
        if img_bytes:
            if st.button(t("analyse",lang), type="primary", key="ana_img"):
                run_analysis(lang,city,lat,lng,db,vclient,components,image_bytes=img_bytes)
        elif st.session_state.get("last_vision"):
            render_result_card(st.session_state["last_vision"], lang)
            if st.session_state.get("rag_result"):
                st.markdown(f"""<div class="ai-box">
                    {st.session_state['rag_result']['answer'].replace(chr(10),'<br>')}
                </div>""", unsafe_allow_html=True)
            render_review(db, st.session_state["last_vision"], lang)

    # ── TEXT ────────────────────────────────────────────────────
    elif mode == "text":
        txt = st.text_area(t("txt_ph",lang), placeholder=t("txt_ph",lang),
                           height=95, label_visibility="collapsed", key="txt_inp")
        if txt.strip():
            if st.button(t("analyse",lang), type="primary", key="ana_txt"):
                run_analysis(lang,city,lat,lng,db,vclient,components,text_input=txt.strip())

    # ── VOICE ───────────────────────────────────────────────────
    elif mode == "voice":
        whisper = get_whisper()
        st.markdown(f"""<div class="voice-box">
            <div style="font-size:2rem;margin-bottom:0.4rem">🎤</div>
            <div style="color:#334155;font-weight:600;font-size:0.9rem">
                {t('voice_hint',lang)}</div>
        </div>""", unsafe_allow_html=True)
        if whisper:
            audio = st.audio_input("Record", label_visibility="collapsed")
            if audio:
                with st.spinner("🎤 Transcribing…"):
                    from voice import speech_to_text
                    text = speech_to_text(whisper, audio.getvalue(), lang)
                if text:
                    st.success(f"📝 You said: *{text}*")
                    run_analysis(lang,city,lat,lng,db,vclient,components,text_input=text)
                else:
                    st.warning("⚠️ Could not transcribe. Please speak clearly and try again.")
        else:
            st.warning("⚠️ Voice model unavailable. Use Image or Text mode instead.")

    else:
        st.markdown("""<div style="text-align:center;padding:2.5rem;color:#94a3b8">
            <div style="font-size:3.5rem;margin-bottom:0.8rem">📸</div>
            <div style="font-family:Syne,sans-serif;font-size:0.95rem;color:#64748b">
                Choose an input method above to get started</div>
            <div style="margin-top:0.4rem;font-size:0.83rem">اوپر سے ان پٹ کا طریقہ منتخب کریں</div>
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB: JUDGE DEMO
# ════════════════════════════════════════════════════════════
def render_demo_tab(lang, vclient, components):
    st.markdown(f"""<div style="background:linear-gradient(135deg,#14532d,#16a34a);
        border-radius:var(--r-lg);padding:1.4rem 1.8rem;margin-bottom:1.2rem">
        <h3 style="color:white;margin:0;font-family:Syne,sans-serif">🎯 Judge Demo Panel</h3>
        <p style="margin:0.3rem 0 0;color:#dcfce7;font-size:0.87rem">
            Pre-loaded waste images — click any to run full AI analysis instantly</p>
    </div>""", unsafe_allow_html=True)

    active = st.session_state.get(tk("demo_images"),False)
    if st.button(t("hide_demo",lang) if active else t("show_demo",lang),
                 type="primary" if active else "secondary", key="demo_toggle"):
        st.session_state[tk("demo_images")] = not active; st.rerun()

    if not active:
        st.markdown("""<div style="text-align:center;padding:2rem;background:white;
            border-radius:var(--r-md);border:1px solid var(--border);color:#94a3b8;margin-top:1rem">
            <div style="font-size:2.5rem">🎯</div>
            <div style="font-family:Syne,sans-serif;font-size:0.92rem;margin-top:0.5rem">
                Click "Show Demo Images" to reveal pre-loaded test images</div>
        </div>""", unsafe_allow_html=True)
        return

    st.markdown(f"**{t('demo_try',lang)}**")
    st.markdown("---")
    cols   = st.columns(5)
    sel    = None
    for i,demo in enumerate(DEMO_IMAGES):
        with cols[i]:
            try: st.image(demo["url"], use_container_width=True)
            except: st.markdown(f"<div style='text-align:center;font-size:3rem'>{demo['emoji']}</div>",unsafe_allow_html=True)
            st.markdown(f"""<div style="text-align:center;padding:0.3rem 0">
                <div style="font-weight:700;font-size:0.82rem;color:#0f172a">{demo['emoji']} {demo['label']}</div>
                <div style="color:#94a3b8;font-size:0.72rem">{demo['hint']}</div>
            </div>""", unsafe_allow_html=True)
            if st.button("Test", key=f"d_{i}", use_container_width=True): sel = demo

    if sel:
        import requests
        st.markdown("---")
        st.info(f"🔍 Testing: **{sel['label']}**")
        try:
            r = requests.get(sel["url"], timeout=10)
            run_analysis("english","Demo",0,0,None,vclient,components,image_bytes=r.content)
        except Exception as e: st.error(f"Demo error: {e}")


# ════════════════════════════════════════════════════════════
# TAB: TEAM
# ════════════════════════════════════════════════════════════
def render_team_tab(lang):
    st.markdown(f"""<div style="text-align:center;padding:1.5rem 1rem 1rem">
        <h2 style="font-family:Syne,sans-serif;color:#0f172a;font-size:1.75rem;margin:0">
            {t('team_title',lang)}</h2>
        <p style="color:#64748b;margin:0.35rem 0 0">{t('team_sub',lang)}</p>
        <div style="width:48px;height:4px;background:linear-gradient(90deg,#166534,#22c55e);
                    border-radius:2px;margin:0.75rem auto 1.5rem"></div>
    </div>""", unsafe_allow_html=True)

    cols = st.columns(5)
    for i,member in enumerate(TEAM):
        with cols[i]:
            if member:
                li = member.get("linkedin",""); gh = member.get("github","")
                ac = member.get("academic","")
                links = ""
                if li: links += f'<a href="{li}" target="_blank" class="t-link" title="LinkedIn">in LinkedIn</a>'
                if gh: links += f'<a href="{gh}" target="_blank" class="t-link" title="GitHub">⌥ GitHub</a>'
                st.markdown(f"""<div class="team-card">
                    <div class="t-avatar">{member['initials']}</div>
                    <div class="t-name">{member['name']}</div>
                    <div class="t-role">{member['role']}</div>
                    {"<div class='t-acad'>"+ac+"</div>" if ac else ""}
                    <div class="t-links">{links}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="t-ph">
                    <div style="font-size:1.8rem;margin-bottom:0.4rem">👤</div>
                    <div style="font-weight:600;font-size:0.85rem">{t('coming',lang)}</div>
                    <div style="font-size:0.75rem;margin-top:0.2rem;color:#cbd5e1">Member {i+1}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""<div style="background:linear-gradient(135deg,#14532d,#166534);
        border-radius:var(--r-lg);padding:1.5rem 2rem">
        <h4 style="color:white;margin:0 0 0.9rem;font-family:Syne,sans-serif">🌿 About This Project</h4>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;font-size:0.87rem">
            <div><strong style="color:#86efac">🎯 Mission</strong><br>
                <span style="color:rgba(255,255,255,0.82)">Turn Pakistan's waste into economic opportunity using AI</span></div>
            <div><strong style="color:#86efac">🛠️ Tech Stack</strong><br>
                <span style="color:rgba(255,255,255,0.82)">Llama 4 Vision · Llama 3.3-70B · FAISS · Streamlit</span></div>
            <div><strong style="color:#86efac">🗄️ Data Layer</strong><br>
                <span style="color:rgba(255,255,255,0.82)">Google Sheets · Qdrant GPS · Cloudinary</span></div>
            <div><strong style="color:#86efac">🌍 Impact</strong><br>
                <span style="color:rgba(255,255,255,0.82)">Helping kabariwalas access real market intelligence</span></div>
        </div>
    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("## ♻️ Eco AI")
        st.markdown("---")

        st.markdown("### 🌐 Language")
        language = st.radio("lang_r",["english","urdu"],
            format_func=lambda x:"🇬🇧 English" if x=="english" else "🇵🇰 اردو",
            horizontal=True, label_visibility="collapsed")
        st.markdown("---")

        st.markdown("### 📍 Location")
        city = st.text_input(t("city",language), value="Lahore",
                             placeholder="Lahore, Karachi…")
        c1,c2 = st.columns(2)
        with c1: lat = st.number_input(t("lat",language),value=31.5204,format="%.4f",step=0.0001)
        with c2: lng = st.number_input(t("lng",language),value=74.3587,format="%.4f",step=0.0001)

        # Auto GPS via streamlit-js-eval
        try:
            from streamlit_js_eval import get_geolocation
            if st.button("📡 Auto-Detect GPS", use_container_width=True, key="gps_btn"):
                loc = get_geolocation()
                if loc and loc.get("coords"):
                    lat = loc["coords"]["latitude"]
                    lng = loc["coords"]["longitude"]
                    st.success(f"📍 {lat:.4f}, {lng:.4f}")
        except: pass
        st.markdown("---")

        st.markdown("### 📊 Stats")
        try:
            db = get_db()
            from database import get_recent_scans
            recent  = get_recent_scans(db, limit=100)
            today   = datetime.now().strftime("%Y-%m-%d")
            today_n = sum(1 for s in recent if s.get("timestamp","").startswith(today))
            st.metric("Today", today_n); st.metric("Total", len(recent))
        except:
            st.metric("Today","—"); st.metric("Total","—")
        st.markdown("---")

        user = st.session_state.get("current_user")
        if user and user.get("user_id")!="GUEST":
            st.markdown(f"**👤 {user.get('name','')}**\n\n`{user.get('user_id','')}`")
            if st.button("🚪 Switch User", key="sw_u"):
                for k in ["current_user","save_preference","last_vision","rag_result",
                          "review_submitted","show_id_popup"]:
                    st.session_state[k] = None
                st.rerun()
            st.markdown("---")

        with st.expander("ℹ️ About"):
            st.markdown("""
**Eco AI** turns Pakistan's waste into wealth.
- 🦙 Llama 4 Scout Vision (Groq)
- 🤖 Llama 3.3-70B RAG (Groq)
- 🔍 FAISS vector search
- 🗄️ Sheets + Qdrant + Cloudinary
- 🎤 Whisper STT + gTTS TTS
            """)

    return language, city, lat, lng


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════
def main():
    init_state()
    db = get_db()

    # Show modal first — blocks until complete
    render_user_modal(db)
    render_id_popup()
    if not st.session_state.get("current_user"): return

    language, city, lat, lng = render_sidebar()

    # Header
    st.markdown(f"""<div class="eco-header">
        <h1>{t('title',language)}</h1>
        <p>{t('subtitle',language)}</p>
    </div>""", unsafe_allow_html=True)

    render_user_bar(language)

    vclient    = get_vclient()
    components = get_rag()

    scan_tab, demo_tab, team_tab = st.tabs([
        t("tab_scan",language), t("tab_demo",language), t("tab_team",language),
    ])
    with scan_tab:
        render_scan_tab(language, city, lat, lng, vclient, components, db)
    with demo_tab:
        render_demo_tab(language, vclient, components)
    with team_tab:
        render_team_tab(language)


if __name__ == "__main__":
    main()
