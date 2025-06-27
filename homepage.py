import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="智慧承保風險評估平台",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed" # 首頁通常不需要一直顯示側邊欄
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* General body styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    /* Title */
    .title {
        text-align: center;
        font-size: 2.8em;
        font-weight: bold;
        color: #003366; /* Dark Blue */
        margin-bottom: 0.5rem;
    }
    /* Subtitle / Description */
    .description {
        text-align: center;
        font-size: 1.3em;
        color: #333333;
        margin-bottom: 3rem;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }
    /* Feature Cards */
    .feature-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-left: 5px solid #FFB300; /* Gold accent */
        border-radius: 8px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        height: 100%; /* Ensure cards in a row have same height */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
    }
    .feature-card h3 {
        font-size: 1.6em;
        font-weight: bold;
        color: #004080; /* Darker Blue */
        margin-bottom: 0.8rem;
    }
    .feature-card p {
        font-size: 1.05em;
        color: #555555;
        line-height: 1.6;
        flex-grow: 1;
    }
    .feature-card .icon {
        font-size: 2.5em;
        margin-right: 0.8rem;
        color: #FFB300; /* Gold */
    }
    /* Button Styling */
    .stButton>button { /* Targeting Streamlit's default button class */
        display: block;
        margin: 3rem auto 1rem auto; /* Center button and add top margin */
        padding: 0.8rem 2.5rem;
        font-size: 1.2em;
        font-weight: bold;
        color: #FFFFFF;
        background-color: #005A9C; /* Primary Blue */
        border: none;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        transition: background-color 0.2s ease, transform 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #004080; /* Darker Blue on hover */
        transform: translateY(-2px);
    }
    .stButton>button:active {
        background-color: #003366;
        transform: translateY(0px);
    }
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown("<div class='title'>智慧承保風險評估平台</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='description'>"
    "運用先進 AI 技術，提供全面、即時的客戶風險畫像與智能分析，"
    "助力保險機構實現更精準、高效的承保決策。"
    "</div>",
    unsafe_allow_html=True
)

# --- Features Section ---
st.markdown("<h2 style='text-align: center; color: #003366; margin-bottom: 2rem;'>核心功能特色</h2>", unsafe_allow_html=True)

cols = st.columns(3, gap="large")

with cols[0]:
    st.markdown(
        """
        <div class="feature-card">
            <div>
                <h3><span class="icon">👤</span>客戶風險畫像</h3>
                <p>整合多維度數據，構建客戶360°風險視圖，深入洞察潛在風險，為每一位客戶提供精準的風險評級。</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with cols[1]:
    st.markdown(
        """
        <div class="feature-card">
            <div>
                <h3><span class="icon">💡</span>AI 智能分析</h3>
                <p>強大的 AI 引擎，自動化評估數百個複雜風險因子，提供客觀、科學的分析結果，有效識別高風險案件。</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with cols[2]:
    st.markdown(
        """
        <div class="feature-card">
            <div>
                <h3><span class="icon">📊</span>即時決策輔助</h3>
                <p>快速生成清晰易懂的承保建議與風險報告，顯著提升人工審核效率，優化整體業務處理流程。</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Call to Action Button ---
if st.button("🚀 開始分析之旅"):
    st.switch_page("pages/analysis_page.py")

st.markdown("---")
st.markdown("<p style='text-align:center; color: #888;'>© 2024 智慧承保解決方案</p>", unsafe_allow_html=True)
