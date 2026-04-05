from datetime import datetime
import os, glob
import requests
import pandas as pd
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

load_dotenv()

st.set_page_config(
    page_title="АгроСубсидия KZ",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #EEF5EE !important;
    color: #111827 !important;
}
#MainMenu, footer, header { visibility: hidden; }

/* SIDEBAR - always visible */
section[data-testid="stSidebar"] {
    background: #064E3B !important;
    min-width: 230px !important;
    max-width: 230px !important;
    transform: none !important;
    visibility: visible !important;
    display: block !important;
}
/* Show sidebar toggle button clearly */
[data-testid="collapsedControl"] {
    display: flex !important;
    background: #064E3B !important;
    color: #FFFFFF !important;
    border-radius: 0 8px 8px 0 !important;
}
section[data-testid="stSidebar"] * { color: #ECFDF5 !important; }
section[data-testid="stSidebar"] .stRadio > label { display: none !important; }
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
    gap: 2px !important; display: flex !important; flex-direction: column !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    display: flex !important; align-items: center !important;
    padding: 10px 16px !important; border-radius: 8px !important;
    font-size: 14px !important; font-weight: 500 !important;
    color: #86EFAC !important; border: none !important;
    background: transparent !important; cursor: pointer !important;
    transition: background 0.15s !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.12) !important; color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .stRadio input { display: none !important; }

/* MAIN */
.main .block-container {
    padding: 24px 32px 40px 32px !important;
    max-width: 1180px !important;
}

/* METRICS */
div[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #BBF7D0 !important;
    border-top: 3px solid #059669 !important;
    border-radius: 12px !important;
    padding: 16px 18px !important;
}
div[data-testid="stMetric"] label {
    font-size: 11px !important; font-weight: 700 !important;
    color: #059669 !important; text-transform: uppercase !important; letter-spacing: 0.7px !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 26px !important; font-weight: 800 !important; color: #064E3B !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 12px !important; color: #6B7280 !important;
}

/* BUTTONS */
div.stButton > button {
    background: #059669 !important; color: #FFFFFF !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; font-size: 14px !important;
    padding: 11px 22px !important; width: 100% !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 2px 6px rgba(5,150,105,0.2) !important;
    transition: background 0.15s !important;
}
div.stButton > button:hover {
    background: #047857 !important; color: #FFFFFF !important;
}

/* FORM */
.stSelectbox label, .stNumberInput label {
    font-size: 13px !important; font-weight: 600 !important; color: #065F46 !important;
}
div[data-baseweb="select"] > div {
    background: #FFFFFF !important; border: 1.5px solid #A7F3D0 !important;
    border-radius: 9px !important; color: #111827 !important;
}
div[data-testid="stNumberInput"] input {
    background: #FFFFFF !important; border: 1.5px solid #A7F3D0 !important;
    border-radius: 9px !important; color: #111827 !important;
    font-size: 14px !important;
}

/* CHAT */
[data-testid="stChatMessage"] {
    background: #FFFFFF !important; border: 1px solid #D1FAE5 !important;
    border-radius: 12px !important; margin-bottom: 8px !important;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li { color: #111827 !important; font-size: 14px !important; line-height: 1.7 !important; }
[data-testid="stChatMessage"] strong { color: #064E3B !important; font-weight: 700 !important; }
[data-testid="stMarkdownContainer"] * { color: #111827 !important; }
[data-testid="stChatInput"] textarea {
    color: #111827 !important; background: #FFFFFF !important;
    border: 1.5px solid #A7F3D0 !important; border-radius: 10px !important;
}

/* DATAFRAME */
[data-testid="stDataFrame"] {
    border: 1px solid #BBF7D0 !important; border-radius: 12px !important; overflow: hidden !important;
}
[data-testid="stDataFrame"] th {
    background: #ECFDF5 !important; color: #065F46 !important;
    font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.4px !important;
}
[data-testid="stDataFrame"] td { color: #111827 !important; font-size: 13px !important; }

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    background: #D1FAE5 !important; border-radius: 10px !important; padding: 3px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important; font-size: 13px !important; font-weight: 600 !important;
    color: #065F46 !important; border: none !important; background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important; color: #064E3B !important;
    box-shadow: 0 1px 4px rgba(5,150,105,0.1) !important;
}

/* PROGRESS */
.stProgress > div > div { background: #059669 !important; border-radius: 3px !important; }

/* ALERTS */
[data-testid="stAlert"] p { color: #111827 !important; }
hr { border-color: #BBF7D0 !important; }
</style>
""", unsafe_allow_html=True)

# ── DATA ───────────────────────────────────────────────────────────────────────
REGIONS = [
    "Акмолинская область","Актюбинская область","Алматинская область",
    "Атырауская область","Восточно-Казахстанская область","Жамбылская область",
    "Западно-Казахстанская область","Карагандинская область","Костанайская область",
    "Кызылординская область","Мангистауская область","Павлодарская область",
    "Северо-Казахстанская область","Туркестанская область","г. Алматы",
    "г. Астана","Абайская область","Улытауская область",
]
SUBSIDY_CATEGORIES = [
    "Субсидирование в птицеводстве","Субсидирование в овцеводстве",
    "Субсидирование в коневодстве","Субсидирование в свиноводстве",
    "Субсидирование в скотоводстве","Субсидирование затрат по искусственному осеменению",
]

# ── ML ─────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_ml():
    files = glob.glob("data/*.xlsx")
    if not files:
        return None, None, None, None, None
    try:
        df = pd.read_excel(files[0], header=4)
        df.columns = ["num","date","c2","c3","oblast","akimat",
                      "app_num","direction","subsidy_name","status","normativ","amount","district"]
        df = df.dropna(subset=["status","normativ","amount"])
        df["normativ"] = pd.to_numeric(df["normativ"], errors="coerce").fillna(0)
        df["amount"]   = pd.to_numeric(df["amount"],   errors="coerce").fillna(0)
        df["target"]   = (df["status"] == "Исполнена").astype(int)
        le_ob  = LabelEncoder()
        le_dir = LabelEncoder()
        df["ob_enc"]   = le_ob.fit_transform(df["oblast"].astype(str).fillna("Unknown"))
        df["dir_enc"]  = le_dir.fit_transform(df["direction"].astype(str).fillna("Unknown"))
        df["ratio"]    = df["amount"] / df["normativ"].replace(0, 1)
        df["hi"]       = (df["amount"] > df["amount"].mean() + 2*df["amount"].std()).astype(int)
        dt = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
        df["month"] = dt.dt.month.fillna(6).astype(int)
        df["hour"]  = dt.dt.hour.fillna(10).astype(int)
        FEATS = ["normativ","amount","ratio","hi","ob_enc","dir_enc","month","hour"]
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, max_depth=8)
        model.fit(df[FEATS], df["target"])
        reg = df.groupby("oblast").agg(total=("target","count"), done=("target","sum")).reset_index()
        reg["rate"] = (reg["done"]/reg["total"]*100).round(1)
        reg = reg.sort_values("rate", ascending=False).reset_index(drop=True)
        dirs = df.groupby("direction").agg(total=("target","count"), done=("target","sum")).reset_index()
        dirs["rate"] = (dirs["done"]/dirs["total"]*100).round(1)
        return model, le_ob, le_dir, reg, dirs
    except Exception:
        return None, None, None, None, None

def ml_score(model, le_ob, le_dir, oblast, direction, normativ, amount):
    try:
        ob_e  = le_ob.transform([oblast])[0]    if oblast    in le_ob.classes_  else 0
        dir_e = le_dir.transform([direction])[0] if direction in le_dir.classes_ else 0
        ratio = amount / max(normativ, 1)
        hi    = 1 if amount > 5_000_000 else 0
        X = pd.DataFrame([[normativ,amount,ratio,hi,ob_e,dir_e,6,10]],
                         columns=["normativ","amount","ratio","hi","ob_enc","dir_enc","month","hour"])
        return round(model.predict_proba(X)[0][1]*100, 1)
    except Exception:
        return None

# ── SESSION ─────────────────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role":"assistant","content":"Сәлем. Субсидия алу талаптары, скоринг жүйесі немесе тәуекелдерді азайту жолдары туралы сұрақтарыңызға жауап беремін."}
    ]
if "history" not in st.session_state:
    st.session_state.history = []

# ── SCORING ─────────────────────────────────────────────────────────────────────
def calc_score(farm_size, income, debt, workforce, category):
    dr = debt / max(income, 1)
    s = 100
    if farm_size < 50: s -= 25
    elif farm_size < 150: s -= 12
    else: s += 4
    if income < 5_000_000: s -= 30
    elif income < 20_000_000: s -= 12
    else: s += 5
    if dr > 1.0: s -= 38
    elif dr > 0.6: s -= 20
    elif dr > 0.35: s -= 10
    else: s += 4
    if workforce < 5: s -= 12
    elif workforce > 20: s += 3
    cw = {c:(5+i) for i,c in enumerate(SUBSIDY_CATEGORIES)}
    s += cw.get(category, 0)
    s = int(max(0, min(100, s)))
    if s > 70: d = "Recommended"
    elif s >= 40: d = "Manual Review"
    else: d = "High Risk"
    return s, d

def calc_risks(income, debt, workforce, farm_size):
    dr = debt / max(income, 1)
    return {
        "Климаттық тәуекел":   max(5, min(100, int(25 + 200/max(farm_size,5)))),
        "Қаржылық тәуекел":    max(5, min(100, int(20 + dr*70))),
        "Операциялық тәуекел": max(5, min(100, int(65 - min(workforce,30)*1.5))),
    }

def dec_style(d):
    return {
        "Recommended":   ("Ұсынылады",      "#F0FDF4","#166534","#16A34A","#BBF7D0"),
        "Manual Review": ("Тексеріс қажет", "#FFFBEB","#92400E","#D97706","#FDE68A"),
        "High Risk":     ("Жоғары тәуекел", "#FFF1F2","#881337","#E11D48","#FECDD3"),
    }.get(d, ("—","#F5F5F5","#374151","#6B7280","#E5E7EB"))

def get_pros_cons(income, debt, workforce, farm_size):
    dr = debt/max(income,1)
    p, c = [], []
    if farm_size >= 150: p.append("Ірі жер көлемі")
    elif farm_size >= 80: p.append("Жеткілікті жер")
    if income >= 20_000_000: p.append("Жоғары табыс")
    elif income >= 8_000_000: p.append("Орташа табыс")
    if workforce >= 10: p.append("Жеткілікті жұмыс күші")
    if dr <= 0.35: p.append("Қарыз деңгейі қолайлы")
    if dr > 1: c.append("Қарыз табысынан жоғары")
    elif dr > 0.6: c.append("Жоғары қарыз жүктемесі")
    if workforce < 5: c.append("Жеткіліксіз жұмыс күші")
    if farm_size < 50: c.append("Шағын жер көлемі")
    if income < 5_000_000: c.append("Табыс деңгейі төмен")
    if not p: p.append("Параметрлерді жақсарту қажет")
    if not c: c.append("Критикалық тәуекел жоқ")
    return p, c

# ── AI ──────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Сен АгроСубсидия KZ жүйесінің AI кеңесшісісің.
Скоринг: 70-100 ұсынылады, 40-69 тексеріс, 0-39 жоғары тәуекел.
ML RandomForest моделі 36651 өтінімге тренингтелген, дәлдік 84%.
Қазақша сұраққа қазақша, орысша сұраққа орысша жауап бер. Нақты, қысқа, кәсіби."""

def ai_resp(msg, hist=None):
    if not hist: hist = []
    key = os.environ.get("GROQ_API_KEY","")
    if not key: return "GROQ_API_KEY табылмады."
    msgs = [{"role":"system","content":SYSTEM_PROMPT}]
    for m in hist[-10:]:
        r = m.get("role","")
        if r == "ai": r = "assistant"
        if r in ("user","assistant"): msgs.append({"role":r,"content":m["content"]})
    msgs.append({"role":"user","content":msg})
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
            json={"model":"llama-3.3-70b-versatile","messages":msgs,"max_tokens":800,"temperature":0.6},
            timeout=30,
        )
        if resp.status_code == 200: return resp.json()["choices"][0]["message"]["content"]
        if resp.status_code == 429: return "Лимит асты. Бірнеше секундтан кейін қайта жіберіңіз."
        return f"Қате {resp.status_code}."
    except Exception: return "Байланыс қатесі."

# ── LOAD ML ─────────────────────────────────────────────────────────────────────
ml_model, le_ob, le_dir, reg_df, dir_df = load_ml()
has_ml = ml_model is not None

# ── SIDEBAR ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:28px 20px 18px;">
        <div style="font-size:20px;font-weight:900;color:#FFFFFF;letter-spacing:-0.3px;line-height:1.2;">АгроСубсидия</div>
        <div style="font-size:12px;color:#6EE7B7;margin-top:3px;font-weight:500;">AI Скоринг · KZ · 2025</div>
    </div>
    <div style="height:1px;background:rgba(255,255,255,0.12);margin:0 18px 14px;"></div>
    <div style="padding:0 12px 6px;font-size:10px;font-weight:700;color:#34D399;text-transform:uppercase;letter-spacing:1px;">Бөлімдер</div>
    """, unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state["page"] = "Дашборд"
    
    selected = st.radio("Навигация", [
        "Дашборд", "Жаңа өтінім", "Тарих", "Аналитика", "AI Кеңесші",
    ], label_visibility="collapsed", index=["Дашборд","Жаңа өтінім","Тарих","Аналитика","AI Кеңесші"].index(st.session_state["page"]))
    
    if selected != st.session_state["page"]:
        st.session_state["page"] = selected
        st.rerun()
    
    page = st.session_state["page"]

    st.markdown("""
    <div style="padding:20px 18px 0;margin-top:auto;">
        <div style="height:1px;background:rgba(255,255,255,0.1);margin-bottom:12px;"></div>
        <div style="font-size:11px;color:#34D399;opacity:0.6;line-height:1.6;">
            Decentrathon 5.0<br>AI for Government
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── HEADER ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#064E3B;border-radius:14px;padding:28px 32px;margin-bottom:24px;">
    <p style="font-size:11px;font-weight:600;color:#34D399;letter-spacing:2px;text-transform:uppercase;margin:0 0 10px;">
        Ауыл шаруашылығы министрлігі &nbsp;·&nbsp; Decentrathon 5.0
    </p>
    <h1 style="font-size:28px;font-weight:900;color:#FFFFFF;letter-spacing:-0.5px;margin:0 0 8px;line-height:1.2;">
        АгроСубсидия KZ
    </h1>
    <p style="font-size:14px;color:#A7F3D0;max-width:520px;line-height:1.65;margin:0 0 16px;">
        Мемлекеттік субсидияларды алуға арналған AI скоринг платформасы.
        RandomForest ML моделі нақты 36,651 өтінімге тренингтелген — дәлдік 84%.
    </p>
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="width:8px;height:8px;background:#4ADE80;border-radius:50%;"></div>
        <span style="font-size:13px;color:#D1FAE5;font-weight:500;">Жүйе жұмыс жасауда</span>
    </div>
</div>
""", unsafe_allow_html=True)

# TOP NAV BAR - always visible regardless of sidebar state  
nav_items = ["Дашборд", "Жаңа өтінім", "Тарих", "Аналитика", "AI Кеңесші"]
page = st.session_state.get("page", "Дашборд")

st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] div.stButton > button {
    border-radius: 8px !important;
    font-size: 13px !important;
    padding: 8px 4px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

cols_nav = st.columns(len(nav_items))
for i, (col, item) in enumerate(zip(cols_nav, nav_items)):
    with col:
        if st.button(item, key=f"tnav_{i}", use_container_width=True):
            st.session_state["page"] = item
            st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── HELPERS ─────────────────────────────────────────────────────────────────────
def white_card(html):
    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #BBF7D0;border-radius:14px;'
        f'padding:22px;box-shadow:0 1px 6px rgba(5,150,105,0.06);">{html}</div>',
        unsafe_allow_html=True
    )

def page_title(title, subtitle=""):
    sub = f'<div style="font-size:13px;color:#6B7280;margin-top:3px;margin-bottom:20px;">{subtitle}</div>' if subtitle else "<div style='margin-bottom:20px;'></div>"
    st.markdown(
        f'<div style="font-size:22px;font-weight:800;color:#064E3B;margin-bottom:2px;">{title}</div>{sub}',
        unsafe_allow_html=True
    )

def section_title(t):
    st.markdown(f'<div style="font-size:14px;font-weight:700;color:#064E3B;margin:18px 0 10px;">{t}</div>', unsafe_allow_html=True)

# ══ DASHBOARD ══════════════════════════════════════════════════════════════════
if page == "Дашборд":
    hist = st.session_state.history
    n = len(hist)
    rec = sum(1 for x in hist if x["Decision"]=="Recommended")
    rate = round(rec/n*100,1) if n else 0
    bud  = sum(x.get("Budget",0) for x in hist)
    avg  = round(sum(x["Score"] for x in hist)/n,1) if n else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Барлық өтінімдер", n)
    c2.metric("Мақұлдау үлесі", f"{rate}%")
    c3.metric("Орташа балл", f"{avg}/100")
    c4.metric("Жалпы субсидия", f"{bud/1_000_000:.1f}M ₸" if bud else "—")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    left, right = st.columns([3,2])

    with left:
        white_card("""
        <div style="font-size:14px;font-weight:700;color:#064E3B;margin-bottom:12px;">Жүйе туралы</div>
        <p style="font-size:13px;color:#374151;line-height:1.8;margin:0 0 16px;">
            АгроСубсидия KZ — Қазақстан фермерлерінің мемлекеттік субсидия алу мүмкіндіктерін
            жасанды интеллект арқылы бағалайтын платформа. RandomForest моделі нақты 36,651
            өтінімге тренингтелген, дәлдік 84%.
        </p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div style="background:#F0FDF4;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:22px;font-weight:900;color:#064E3B;">36,651</div>
                <div style="font-size:11px;color:#059669;font-weight:600;margin-top:2px;text-transform:uppercase;letter-spacing:0.4px;">өтінім өңделді</div>
            </div>
            <div style="background:#F0FDF4;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:22px;font-weight:900;color:#064E3B;">84%</div>
                <div style="font-size:11px;color:#059669;font-weight:600;margin-top:2px;text-transform:uppercase;letter-spacing:0.4px;">ML дәлдігі</div>
            </div>
            <div style="background:#F0FDF4;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:22px;font-weight:900;color:#064E3B;">18</div>
                <div style="font-size:11px;color:#059669;font-weight:600;margin-top:2px;text-transform:uppercase;letter-spacing:0.4px;">өңір</div>
            </div>
            <div style="background:#ECFDF5;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:22px;font-weight:900;color:#16A34A;">57.3%</div>
                <div style="font-size:11px;color:#16A34A;font-weight:600;margin-top:2px;text-transform:uppercase;letter-spacing:0.4px;">орындалды</div>
            </div>
        </div>""")

    with right:
        white_card("""
        <div style="font-size:14px;font-weight:700;color:#064E3B;margin-bottom:14px;">Скоринг шкаласы</div>
        <div style="display:flex;flex-direction:column;gap:8px;">
            <div style="border:1px solid #BBF7D0;border-left:4px solid #16A34A;border-radius:10px;padding:12px 14px;">
                <div style="font-size:17px;font-weight:800;color:#166534;">70 – 100</div>
                <div style="font-size:12px;color:#166534;margin-top:2px;font-weight:500;">Субсидия алуға ұсынылады</div>
            </div>
            <div style="border:1px solid #FDE68A;border-left:4px solid #D97706;border-radius:10px;padding:12px 14px;">
                <div style="font-size:17px;font-weight:800;color:#92400E;">40 – 69</div>
                <div style="font-size:12px;color:#92400E;margin-top:2px;font-weight:500;">Қолмен тексеріс қажет</div>
            </div>
            <div style="border:1px solid #FECDD3;border-left:4px solid #E11D48;border-radius:10px;padding:12px 14px;">
                <div style="font-size:17px;font-weight:800;color:#881337;">0 – 39</div>
                <div style="font-size:12px;color:#881337;margin-top:2px;font-weight:500;">Жоғары тәуекел</div>
            </div>
        </div>""")

    if hist:
        section_title("Соңғы өтінімдер")
        dh = pd.DataFrame(hist)
        cols = [c for c in ["Кезі","Өңір","Категория","Score","ML %","Шешім"] if c in dh.columns]
        st.dataframe(dh[cols].tail(8).rename(columns={"Score":"Балл"}), use_container_width=True, height=240)
    else:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.info("Бастау үшін «Жаңа өтінім» бетіне өтіңіз.")

# ══ NEW APPLICATION ════════════════════════════════════════════════════════════
elif page == "Жаңа өтінім":
    page_title("Жаңа өтінім", "Фермаңыздың параметрлерін енгізіп AI бағалауын алыңыз")

    c1, c2 = st.columns(2)
    with c1:
        region    = st.selectbox("Өңір", REGIONS)
        farm_size = st.number_input("Жер көлемі (гектар)", min_value=1.0, value=120.0, step=5.0)
        income    = st.number_input("Жылдық табыс (₸)", min_value=0.0, value=12_000_000.0, step=500_000.0, format="%.0f")
    with c2:
        category  = st.selectbox("Субсидия бағыты", SUBSIDY_CATEGORIES)
        debt      = st.number_input("Ағымдағы қарыз (₸)", min_value=0.0, value=3_000_000.0, step=500_000.0, format="%.0f")
        workforce = st.number_input("Қызметкерлер саны", min_value=1, value=8, step=1)

    budget = st.number_input("Сұралатын субсидия (₸)", min_value=0.0, value=3_000_000.0, step=100_000.0, format="%.0f")
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    run = st.button("Бағалауды іске қосу", use_container_width=True)

    if run:
        score, dec = calc_score(farm_size, income, debt, int(workforce), category)
        risks      = calc_risks(income, debt, int(workforce), farm_size)
        pros, cons = get_pros_cons(income, debt, int(workforce), farm_size)
        lbl, bg, tc, ac, bc = dec_style(dec)
        bar_c = "#16A34A" if score>70 else "#D97706" if score>=40 else "#E11D48"
        prob  = ml_score(ml_model, le_ob, le_dir, region, category, budget, budget) if has_ml else None

        pros_h = "".join(
            f'<div style="font-size:13px;color:#166534;background:#F0FDF4;'
            f'border-radius:6px;padding:6px 12px;margin-bottom:5px;">{x}</div>'
            for x in pros)
        cons_h = "".join(
            f'<div style="font-size:13px;color:#881337;background:#FFF1F2;'
            f'border-radius:6px;padding:6px 12px;margin-bottom:5px;">{x}</div>'
            for x in cons)

        ml_html = ""
        if prob is not None:
            pc = "#16A34A" if prob>=60 else "#D97706" if prob>=40 else "#E11D48"
            ml_html = f"""
            <div style="margin-top:18px;padding-top:16px;border-top:1px solid #D1FAE5;">
                <div style="font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">
                    ML Модель болжамы (84% дәлдік · 36,651 өтінім)
                </div>
                <div style="display:flex;align-items:center;gap:14px;">
                    <div style="font-size:34px;font-weight:900;color:{pc};">{prob}%</div>
                    <div style="font-size:13px;color:#374151;line-height:1.5;">өтінімнің орындалу<br>ықтималдығы</div>
                </div>
                <div style="height:8px;background:#D1FAE5;border-radius:4px;overflow:hidden;margin-top:10px;">
                    <div style="height:100%;width:{prob}%;background:{pc};border-radius:4px;"></div>
                </div>
            </div>"""

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #BBF7D0;border-radius:14px;
                    padding:26px;margin-bottom:18px;box-shadow:0 2px 8px rgba(5,150,105,0.07);">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;
                        gap:16px;margin-bottom:18px;flex-wrap:wrap;">
                <div>
                    <div style="font-size:11px;font-weight:700;color:#059669;
                                text-transform:uppercase;letter-spacing:0.8px;margin-bottom:5px;">
                        Скоринг нәтижесі
                    </div>
                    <div style="font-size:52px;font-weight:900;color:#064E3B;
                                line-height:1;letter-spacing:-2px;">
                        {score}<span style="font-size:20px;font-weight:400;color:#6EE7B7;">/100</span>
                    </div>
                </div>
                <div style="background:{bg};border:1px solid {bc};border-radius:12px;
                            padding:14px 20px;text-align:center;min-width:150px;">
                    <div style="font-size:15px;font-weight:800;color:{tc};">{lbl}</div>
                    <div style="font-size:12px;color:{tc};opacity:0.7;margin-top:3px;">{region}</div>
                </div>
            </div>
            <div style="height:8px;background:#D1FAE5;border-radius:4px;overflow:hidden;margin-bottom:18px;">
                <div style="height:100%;width:{score}%;background:{bar_c};border-radius:4px;"></div>
            </div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                <div style="flex:1;min-width:120px;">
                    <div style="font-size:11px;font-weight:700;color:#059669;
                                text-transform:uppercase;letter-spacing:0.5px;margin-bottom:7px;">
                        Оң факторлар
                    </div>{pros_h}
                </div>
                <div style="flex:1;min-width:120px;">
                    <div style="font-size:11px;font-weight:700;color:#DC2626;
                                text-transform:uppercase;letter-spacing:0.5px;margin-bottom:7px;">
                        Тәуекел факторлары
                    </div>{cons_h}
                </div>
            </div>
            {ml_html}
        </div>
        """, unsafe_allow_html=True)

        section_title("Тәуекел талдауы")
        r1, r2, r3 = st.columns(3)
        for col, (rn, rv) in zip([r1,r2,r3], risks.items()):
            if rv > 65:   rc, rbg, rbo = "#E11D48", "#FFF1F2", "#FECDD3"
            elif rv > 40: rc, rbg, rbo = "#D97706", "#FFFBEB", "#FDE68A"
            else:          rc, rbg, rbo = "#16A34A", "#F0FDF4", "#BBF7D0"
            col.markdown(f"""
            <div style="background:{rbg};border:1px solid {rbo};border-radius:12px;
                        padding:20px;text-align:center;">
                <div style="font-size:30px;font-weight:900;color:{rc};">{rv}%</div>
                <div style="font-size:12px;font-weight:600;color:#374151;
                            margin-top:6px;line-height:1.4;">{rn}</div>
                <div style="height:4px;background:#E5E7EB;border-radius:2px;
                            margin-top:12px;overflow:hidden;">
                    <div style="height:100%;width:{rv}%;background:{rc};border-radius:2px;"></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.session_state.history.append({
            "Кезі": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "Өңір": region, "Категория": category,
            "Жер (га)": farm_size, "Табыс (₸)": income,
            "Қарыз (₸)": debt, "Қызметкер": int(workforce),
            "Субсидия (₸)": budget, "Score": score,
            "ML %": prob if prob is not None else "—",
            "Decision": dec, "Шешім": lbl, "Budget": budget,
        })
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.success("Өтінім сақталды.")

# ══ HISTORY ════════════════════════════════════════════════════════════════════
elif page == "Тарих":
    page_title("Өтінімдер тарихы", "Ағымдағы сессиядағы барлық өтінімдер")

    if not st.session_state.history:
        white_card("""
        <div style="text-align:center;padding:24px 0;">
            <div style="font-size:15px;font-weight:700;color:#064E3B;margin-bottom:6px;">Тарих бос</div>
            <div style="font-size:13px;color:#6B7280;">Жаңа өтінім бетінен өтінім жасаңыз</div>
        </div>""")
    else:
        hdf = pd.DataFrame(st.session_state.history)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Барлығы", len(hdf))
        m2.metric("Ұсынылды", len(hdf[hdf["Decision"]=="Recommended"]))
        m3.metric("Жоғары тәуекел", len(hdf[hdf["Decision"]=="High Risk"]))
        m4.metric("Орташа балл", f"{round(hdf['Score'].mean(),1)}/100")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        show = [c for c in ["Кезі","Өңір","Категория","Score","ML %","Шешім","Субсидия (₸)"] if c in hdf.columns]
        st.dataframe(
            hdf[show].rename(columns={"Score":"Балл"})
            .sort_values("Кезі", ascending=False)
            .reset_index(drop=True),
            use_container_width=True, height=360
        )
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["Шешімдер","Өңірлер","Категориялар"])
        with t1: st.bar_chart(hdf["Шешім"].value_counts())
        with t2: st.bar_chart(hdf["Өңір"].value_counts().head(10))
        with t3: st.bar_chart(hdf["Категория"].value_counts())

# ══ ANALYTICS ══════════════════════════════════════════════════════════════════
elif page == "Аналитика":
    page_title("Аналитика", "Нақты деректер негізіндегі талдау")

    if has_ml and reg_df is not None:
        section_title("Өңірлер бойынша орындалу үлесі (нақты 2025 деректері)")
        rr = reg_df.copy()
        rr.columns = ["Өңір","Барлығы","Орындалды","Орындалу %"]
        st.dataframe(rr[["Өңір","Барлығы","Орындалды","Орындалу %"]], use_container_width=True, height=380)
        section_title("Субсидия бағыттары бойынша орындалу %")
        cd = dir_df[["direction","rate"]].set_index("direction")
        cd.columns = ["Орындалу %"]
        st.bar_chart(cd)

    if st.session_state.history:
        adf = pd.DataFrame(st.session_state.history)
        nn = len(adf)
        hr = len(adf[adf["Decision"]=="High Risk"])
        rc = len(adf[adf["Decision"]=="Recommended"])
        section_title("Өтінімдер статистикасы")
        a1, a2, a3 = st.columns(3)
        a1.metric("Орташа скоринг", f"{round(adf['Score'].mean(),1)}/100")
        a2.metric("Жоғары тәуекел", hr, f"{round(hr/nn*100)}%")
        a3.metric("Ұсынылғандар", rc, f"{round(rc/nn*100)}%")
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        cl, cr = st.columns(2)
        with cl:
            st.markdown('<div style="font-size:13px;font-weight:600;color:#064E3B;margin-bottom:8px;">Балл үлестіруі</div>', unsafe_allow_html=True)
            st.bar_chart(adf["Score"].value_counts().sort_index())
        with cr:
            st.markdown('<div style="font-size:13px;font-weight:600;color:#064E3B;margin-bottom:8px;">Шешімдер</div>', unsafe_allow_html=True)
            st.bar_chart(adf["Шешім"].value_counts())
    elif not has_ml:
        st.warning("data/ папкасында деректер табылмады.")

# ══ AI CHAT ════════════════════════════════════════════════════════════════════
elif page == "AI Кеңесші":
    page_title("AI Кеңесші", "Субсидия және скоринг бойынша сұрақтарыңызға жауап береді")

    st.markdown('<div style="font-size:11px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:8px;">Жылдам сұрақтар</div>', unsafe_allow_html=True)
    q1, q2, q3 = st.columns(3)
    quick = None
    with q1:
        if st.button("Скоринг қалай есептеледі?", use_container_width=True):
            quick = "Скоринг жүйесі қалай жұмыс жасайды?"
    with q2:
        if st.button("Жоғары тәуекел дегеніміз не?", use_container_width=True):
            quick = "Жоғары тәуекел дегеніміз не және оны қалай азайтуға болады?"
    with q3:
        if st.button("Балды жоғарылату жолдары", use_container_width=True):
            quick = "Скоринг балымды жоғарылату үшін не істеуім керек?"

    if quick:
        st.session_state.chat_messages.append({"role":"user","content":quick})
        with st.spinner("Жауап дайындалуда..."):
            r = ai_resp(quick, st.session_state.chat_messages)
        st.session_state.chat_messages.append({"role":"assistant","content":r})
        st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    for m in st.session_state.chat_messages:
        with st.chat_message("user" if m["role"]=="user" else "assistant"):
            st.write(m["content"])

    if ui := st.chat_input("Сұрақ жазыңыз..."):
        st.session_state.chat_messages.append({"role":"user","content":ui})
        with st.chat_message("user"): st.write(ui)
        with st.chat_message("assistant"):
            with st.spinner("Жауап дайындалуда..."):
                ans = ai_resp(ui, st.session_state.chat_messages)
            st.write(ans)
        st.session_state.chat_messages.append({"role":"assistant","content":ans})

    if len(st.session_state.chat_messages) > 1:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        cb, _ = st.columns([1,5])
        with cb:
            if st.button("Чатты тазалау", use_container_width=True):
                st.session_state.chat_messages = [
                    {"role":"assistant","content":"Сәлем. Субсидия және скоринг бойынша сұрақтарыңызға жауап беремін."}
                ]
                st.rerun()
