from datetime import datetime
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="АгроСубсидия | Система оценки",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# MODERN DESIGN - Green/Blue Gradient + Professional Palette
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

        * {
            font-family: 'Poppins', sans-serif;
        }

        html, body {
            background: #F0F7F4;
            color: #1A3A34;
            color-scheme: light;
        }

        .stApp {
            background: linear-gradient(135deg, #F0F7F4 0%, #E8F3F1 100%);
        }

        /* SIDEBAR - Dark Green to Teal Gradient */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0B5345 0%, #0D7377 50%, #14919B 100%);
        }

        section[data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }

        section[data-testid="stSidebar"] h1 {
            font-size: 28px !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            margin-bottom: 5px !important;
        }

        section[data-testid="stSidebar"] h2 {
            color: #E8F3F1 !important;
        }

        /* MAIN CONTENT */
        .main,
        .main * {
            color: #0F172A !important;
        }

        .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
            color: #0F172A !important;
            font-weight: 700 !important;
        }

        .main p, .main span, .main label, .main li, .main td, .main th {
            color: #0F172A !important;
        }

        /* METRICS - Modern Card Style */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #FFFFFF 0%, #F8FCFB 100%);
            border: 1px solid #D4E8E4;
            border-left: 6px solid #0D7377;
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 4px 16px rgba(13, 115, 119, 0.08);
        }

        div[data-testid="stMetric"] label {
            color: #4A7A75 !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        div[data-testid="stMetric"] > div {
            color: #0B5345 !important;
            font-weight: 700 !important;
        }

        /* BUTTONS - Green/Teal Gradient */
        div.stButton > button {
            background: linear-gradient(135deg, #0D7377 0%, #14919B 100%);
            color: #FFFFFF !important;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            padding: 12px 24px;
            font-size: 15px;
            box-shadow: 0 6px 20px rgba(13, 115, 119, 0.25);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        div.stButton > button:hover {
            box-shadow: 0 10px 28px rgba(13, 115, 119, 0.35);
            transform: translateY(-3px);
        }

        div.stButton > button:active {
            transform: translateY(-1px);
        }

        /* SELECTBOX & INPUT FIELDS */
        .stSelectbox label, .stNumberInput label, .stTextInput label {
            color: #0B5345 !important;
            font-weight: 700 !important;
            font-size: 14px !important;
        }

        div[data-testid="stNumberInput"] input,
        div[data-testid="stSelectbox"] select {
            color: #1A3A34 !important;
            background: #FFFFFF !important;
            border: 2px solid #D4E8E4 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            padding: 10px 12px !important;
        }

        /* CARDS & DIVIDERS */
        .section-card {
            background: linear-gradient(135deg, #FFFFFF 0%, #F8FCFB 100%);
            border: 1px solid #D4E8E4;
            border-left: 6px solid #0D7377;
            border-radius: 14px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(13, 115, 119, 0.08);
        }

        .section-card p {
            color: #0F172A !important;
            line-height: 1.6 !important;
        }

        .section-card strong {
            color: #0B5345 !important;
        }

        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] *,
        [data-testid="stChatMessage"],
        [data-testid="stChatMessage"] *,
        [data-testid="stAlert"],
        [data-testid="stAlert"] * {
            color: #0F172A !important;
        }

        [data-testid="stChatMessage"] {
            background: #FFFFFF !important;
            border: 1px solid #D4E8E4 !important;
            border-radius: 12px !important;
        }

        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] div,
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] div {
            color: #0F172A !important;
        }

        hr {
            border-color: #D4E8E4 !important;
        }

        /* STATUS BADGES */
        .status-recommended {
            color: #1B6E2E;
            font-weight: 700;
            font-size: 16px;
            padding: 8px 0;
            background: linear-gradient(135deg, #D4EDDA 0%, #C3E6CB 100%);
            padding: 12px 16px;
            border-radius: 8px;
            display: inline-block;
            border-left: 6px solid #1B6E2E;
        }

        .status-manual {
            color: #B8860B;
            font-weight: 700;
            font-size: 16px;
            padding: 8px 0;
            background: linear-gradient(135deg, #FFF3CD 0%, #FFE69C 100%);
            padding: 12px 16px;
            border-radius: 8px;
            display: inline-block;
            border-left: 6px solid #B8860B;
        }

        .status-reject {
            color: #991B1B;
            font-weight: 700;
            font-size: 16px;
            padding: 8px 0;
            background: linear-gradient(135deg, #F8D7DA 0%, #F5C6CB 100%);
            padding: 12px 16px;
            border-radius: 8px;
            display: inline-block;
            border-left: 6px solid #991B1B;
        }

        /* PROGRESS BAR */
        .stProgress > div > div {
            background: linear-gradient(90deg, #0D7377 0%, #14919B 100%);
        }

        /* DATAFRAME */
        [data-testid="stDataFrame"] {
            border: 1px solid #D4E8E4;
            border-radius: 10px;
        }

        /* TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            border: 2px solid #D4E8E4 !important;
            border-radius: 8px !important;
            color: #2D5B55 !important;
            font-weight: 600 !important;
        }

        .stTabs [aria-selected="true"] {
            border-color: #0D7377 !important;
            color: #0D7377 !important;
        }

        /* DIVIDERS */
        .divider-green {
            height: 3px;
            background: linear-gradient(90deg, #0D7377 0%, #14919B 100%);
            border-radius: 2px;
            margin: 20px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# REAL DATA FROM DATASET
REGIONS = [
    "Акмолинская область",
    "Актюбинская область",
    "Алматинская область",
    "Атырауская область",
    "Восточно-Казахстанская область",
    "Жамбылская область",
    "Западно-Казахстанская область",
    "Карагандинская область",
    "Костанайская область",
    "Кызылординская область",
    "Мангистауская область",
    "Павлодарская область",
    "Северо-Казахстанская область",
    "Туркестанская область",
    "г.Шымкент",
    "область Абай",
    "область Жетісу",
    "область Ұлытау",
]

SUBSIDY_CATEGORIES = [
    "Субсидирование в верблюдоводстве",
    "Субсидирование в козоводстве",
    "Субсидирование в коневодстве",
    "Субсидирование в овцеводстве",
    "Субсидирование в птицеводстве",
    "Субсидирование в пчеловодстве",
    "Субсидирование в свиноводстве",
    "Субсидирование в скотоводстве",
    "Субсидирование затрат по искусственному осеменению",
]

CATEGORY_WEIGHTS = {cat: (5 + i) for i, cat in enumerate(SUBSIDY_CATEGORIES)}

# SESSION STATE
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "ai", "content": "Сәлем! 🌾 Мен АгроСубсидия AI ассистенті. Ферма субсидияларын бағалауға көмектесемін. Сұрақ қойыңыз!"}
    ]

if "history" not in st.session_state:
    st.session_state.history = []


def calculate_score(farm_size: float, income: float, debt: float, workforce: int, category: str) -> tuple[int, str]:
    """Calculate subsidy eligibility score (0-100)."""
    debt_ratio = debt / max(income, 1)
    score = 100

    if farm_size < 50:
        score -= 25
    elif farm_size < 150:
        score -= 12
    else:
        score += 4

    if income < 5_000_000:
        score -= 30
    elif income < 20_000_000:
        score -= 12
    else:
        score += 5

    if debt_ratio > 1.0:
        score -= 38
    elif debt_ratio > 0.6:
        score -= 20
    elif debt_ratio > 0.35:
        score -= 10
    else:
        score += 4

    if workforce < 5:
        score -= 12
    elif workforce > 20:
        score += 3

    score += CATEGORY_WEIGHTS.get(category, 0)
    score = int(max(0, min(100, score)))

    if score > 70:
        decision = "Recommended"
    elif score >= 40:
        decision = "Manual Review"
    else:
        decision = "High Risk"

    return score, decision


def calculate_risks(income: float, debt: float, workforce: int, farm_size: float) -> dict[str, int]:
    """Calculate risk metrics."""
    debt_ratio = debt / max(income, 1)
    climate_risk = min(100, int(25 + (200 / max(farm_size, 5))))
    financial_risk = min(100, int(20 + debt_ratio * 70))
    operational_risk = min(100, int(65 - min(workforce, 30) * 1.5))

    return {
        "Климаттық тәуекел": max(5, climate_risk),
        "Қаржылық тәуекел": max(5, financial_risk),
        "Операциялық тәуекел": max(5, operational_risk),
    }


def get_status_badge(decision: str) -> str:
    """Get status in Kazakh/Russian."""
    badges = {
        "Recommended": "✓ Ұсынылды | Рекомендовано",
        "Manual Review": "⚠ Қолмен тексеру | Ручная проверка",
        "High Risk": "✗ Тәуекел жоғары | Высокий риск",
    }
    return badges.get(decision, decision)


def generate_explanation(score: int, decision: str, income: float, debt: float, workforce: int, farm_size: float) -> str:
    """Generate AI explanation."""
    debt_ratio = debt / max(income, 1)
    
    pros = []
    cons = []

    if farm_size >= 150:
        pros.append("ірілі жер ресурсы")
    elif farm_size >= 80:
        pros.append("жеткілік жер көлемі")

    if income >= 20_000_000:
        pros.append("жақсы табыстық потенциал")
    elif income >= 8_000_000:
        pros.append("орта табыстық деңгей")

    if workforce >= 10:
        pros.append("жеткілік еңбек ресурсы")

    if debt_ratio > 1:
        cons.append("ӨРЕСКЕЛ: Қарыз табысынан артық")
    elif debt_ratio > 0.6:
        cons.append("жоғары қарыз жүктемесі")

    if workforce < 5:
        cons.append("кемінді еңбек ресурсы")

    if farm_size < 50:
        cons.append("шағын жер көлемі")

    if not pros:
        pros.append("жалықсыз мониторинг сағымен ішінде ұсынылуы мүмкін")
    if not cons:
        cons.append("өрескел тәуекелі табылмады")

    decision_kz = {
        "Recommended": "Бекітілуге ұсынылады",
        "Manual Review": "Tексеріс қажет",
        "High Risk": "Жоғары тәуекел",
    }[decision]

    return f"""
**{decision_kz}** | Балл: {score}/100

✓ **Позитивті факторлар:** {', '.join(pros)}

✗ **Тәуекелдер:** {', '.join(cons)}
    """


def get_ai_response(msg: str) -> str:
    """Simple AI chatbot."""
    msg_lower = msg.lower()
    
    if any(w in msg_lower for w in ["кік", "неле", "не", "как", "что"]):
        return "Я АгроСубсидия - система оценки готовности ферм к получению гос. субсидий. Анализирую размер, доход, долги и кадры фермы. Помогу оценить шансы на финансирование."
    
    if any(w in msg_lower for w in ["балл", "скоринг", "баға"]):
        return "Скоринг 0-100: >70 = Рекомендовано, 40-70 = Проверка, <40 = Отказ. Считаю по: земле, доходу, долгам, кадрам и типу хозяйства."
    
    if any(w in msg_lower for w in ["риск", "тәуекел", "опасность"]):
        return "Основные риски: климат, финансовая устойчивость, кадры. Система оценивает каждый и дает рекомендации."
    
    if any(w in msg_lower for w in ["помощь", "как", "істі", "қалай"]):
        return "1️⃣ Раздел 'New Application' 2️⃣ Заполните параметры фермы 3️⃣ Нажмите 'AI-аудит' 4️⃣ Получите оценку и рекомендации"
    
    return "Спасибо за вопрос! Если вопрос о субсидиях или оценке - задайте конкретно, помогу разобраться. 🌾"


# SIDEBAR NAVIGATION
with st.sidebar:
    st.title("🌾 АгроСубсидия")
    st.caption("Система AI-оценки аграрных субсидий")
    st.divider()
    
    page = st.radio(
        "📍 Навигация",
        ["📊 Dashboard", "📝 Новая заявка", "📋 История", "🔬 Аналитика"],
        index=0,
    )

# MAIN HEADER
st.title("🌱 Система оценки аграрных субсидий")
st.markdown(
    "<p style='color: #0F172A; font-size: 16px; margin-top: -10px;'>AI-powered оценка готовности ферм к получению государственных субсидий</p>",
    unsafe_allow_html=True,
)
st.markdown("<div class='divider-green'></div>", unsafe_allow_html=True)


# PAGE: DASHBOARD
if page == "📊 Dashboard":
    total_apps = len(st.session_state.history)
    recommended = sum(1 for x in st.session_state.history if x["Decision"] == "Recommended")
    approval_rate = (recommended / total_apps * 100) if total_apps else 0
    total_budget = sum(x["Requested Budget"] for x in st.session_state.history)

    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Всего заявок", total_apps)
    col2.metric("✓ Процент одобрения", f"{approval_rate:.1f}%")
    col3.metric("💰 Общий бюджет", f"{total_budget:,.0f} ₸")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("О системе")
    st.write(
        "**АгроСубсидия** анализирует параметры вашего хозяйства и выдает объективную оценку шансов на получение государственной поддержки. "
        "Система учитывает размер земли, доходность, уровень долгов, наличие кадров и направление деятельности."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.history:
        recent = pd.DataFrame(st.session_state.history).tail(5)
        st.subheader("📌 Последние заявки")
        st.dataframe(
            recent[["Created At", "Region", "Category", "Score", "Status"]],
            use_container_width=True,
            height=250
        )
    else:
        st.info("💡 Создайте первую заявку, чтобы начать работу")


# PAGE: NEW APPLICATION
elif page == "📝 Новая заявка":
    st.subheader("Создать новую заявку на оценку")

    col_left, col_right = st.columns(2)

    with col_left:
        region = st.selectbox("🗺 Выберите область", REGIONS)
        category = st.selectbox("🏘 Направление хозяйства", SUBSIDY_CATEGORIES)

    with col_right:
        farm_size = st.number_input("📍 Размер участка (гектаров)", min_value=1.0, value=120.0, step=5.0)
        annual_income = st.number_input("💵 Годовой доход (тенге)", min_value=0.0, value=12_000_000.0, step=500_000.0)

    debt = st.number_input("💳 Текущий долг (тенге)", min_value=0.0, value=5_000_000.0, step=500_000.0)
    workforce = st.number_input("👥 Количество сотрудников", min_value=1, value=8, step=1)
    budget = st.number_input("💰 Запрашиваемая субсидия (тенге)", min_value=0.0, value=3_000_000.0, step=100_000.0)

    if st.button("🔍 Запустить AI-оценку", use_container_width=True):
        score, decision = calculate_score(farm_size, annual_income, debt, int(workforce), category)
        risks = calculate_risks(annual_income, debt, int(workforce), farm_size)
        status = get_status_badge(decision)
        explanation = generate_explanation(score, decision, annual_income, debt, int(workforce), farm_size)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("📊 Результаты оценки")

        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.metric("Итоговый балл", f"{score}/100", delta=f"{score - 50} от среднего")
        
        with res_col2:
            if decision == "Recommended":
                st.markdown(f"<p class='status-recommended'>{status}</p>", unsafe_allow_html=True)
            elif decision == "Manual Review":
                st.markdown(f"<p class='status-manual'>{status}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p class='status-reject'>{status}</p>", unsafe_allow_html=True)

        st.markdown(explanation)
        st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("⚠️ Анализ рисков")
        for risk_name, risk_value in risks.items():
            st.write(f"**{risk_name}: {risk_value}%**")
            st.progress(min(risk_value / 100, 1.0))

        st.session_state.history.append({
            "Created At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Region": region,
            "Category": category,
            "Farm Size": farm_size,
            "Annual Income": annual_income,
            "Current Debt": debt,
            "Workforce": int(workforce),
            "Requested Budget": budget,
            "Score": score,
            "Decision": decision,
            "Status": status,
            "Climate Risk": risks["Климаттық тәуекел"],
            "Financial Risk": risks["Қаржылық тәуекел"],
            "Operational Risk": risks["Операциялық тәуекел"],
        })
        st.success("✓ Заявка сохранена!")


# PAGE: HISTORY
elif page == "📋 История":
    st.subheader("История всех заявок")

    if not st.session_state.history:
        st.info("📭 История пуста. Создавайте заявки в разделе 'Новая заявка'")
    else:
        hist_df = pd.DataFrame(st.session_state.history)
        st.dataframe(
            hist_df[["Created At", "Region", "Category", "Score", "Status", "Requested Budget"]],
            use_container_width=True,
            height=400
        )

        st.subheader("📊 Статистика")
        t1, t2, t3 = st.tabs(["По статусам", "По регионам", "По категориям"])

        with t1:
            status_data = hist_df["Status"].value_counts()
            st.bar_chart(status_data)

        with t2:
            region_data = hist_df["Region"].value_counts()
            st.bar_chart(region_data)

        with t3:
            cat_data = hist_df["Category"].value_counts()
            st.bar_chart(cat_data)


# PAGE: ANALYTICS
elif page == "🔬 Аналитика":
    st.subheader("AI Аналитика рисков")

    if not st.session_state.history:
        st.warning("⚠️ Требуется минимум одна заявка. Перейдите в 'Новая заявка'")
    else:
        risk_df = pd.DataFrame(st.session_state.history)

        avg_climate = risk_df["Climate Risk"].mean()
        avg_financial = risk_df["Financial Risk"].mean()
        avg_operational = risk_df["Operational Risk"].mean()

        ac1, ac2, ac3 = st.columns(3)
        ac1.metric("Avg Климат", f"{avg_climate:.0f}%")
        ac2.metric("Avg Финансы", f"{avg_financial:.0f}%")
        ac3.metric("Avg Операции", f"{avg_operational:.0f}%")

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.write("Портфольный анализ помогает оценить общее распределение рисков и планировать стратегию финансирования.")
        st.markdown("</div>", unsafe_allow_html=True)

        chart_df = pd.DataFrame({
            "Риск": ["Климат", "Финансы", "Операции"],
            "Среднее %": [avg_climate, avg_financial, avg_operational]
        })
        st.bar_chart(chart_df.set_index("Риск"), height=400)

        st.subheader("🚨 Случаи высокого риска")
        high_risk = risk_df[risk_df["Decision"] == "High Risk"]
        if len(high_risk) > 0:
            st.dataframe(high_risk[["Created At", "Region", "Score", "Financial Risk"]], use_container_width=True)
        else:
            st.success("✓ Высокорисковых случаев не обнаружено!")


# AI CHAT
st.divider()
st.subheader("💬 AI Консультант")

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("Спросите об оценке или субсидиях..."):
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    ai_resp = get_ai_response(user_input)
    st.session_state.chat_messages.append({"role": "assistant", "content": ai_resp})
    with st.chat_message("assistant"):
        st.write(ai_resp)
