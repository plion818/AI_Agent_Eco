import streamlit as st
import json
import os
import pandas as pd
from collections import OrderedDict
import streamlit.components.v1 as components

# 假設這些模組在同級目錄或PYTHONPATH中
# For a multi-page app, ensure these can be found relative to the main script or are in PYTHONPATH
try:
    from agent_api_client import call_agent_api, extract_final_results, save_results
    import config_rules
    from 中文規則對應 import all_field_zh
    from utils import get_nested_value, get_class_desc_map, get_rule_class_map, get_rule_required_map
except ImportError:
    st.error("無法導入必要的分析模組或工具函數。請確保 agent_api_client.py, config_rules.py, 中文規則對應.py 和 utils.py 在正確的路徑。")
    st.stop()

def load_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"CSS file not found: {file_name}")
        return ""

# Load CSS from the central file
# Note: The path to 'assets/styles.css' needs to be correct from the 'pages' directory.
# If 'assets' is at the root, and this script is in 'pages', the path should be '../assets/styles.css'.
# However, Streamlit typically serves assets from a static directory if configured,
# or paths are relative to the main script (homepage.py).
# For simplicity with st.markdown, using a relative path from where homepage.py is run is often easiest.
# Let's assume homepage.py and assets/ are at the same level.
# If running analysis_page.py directly, this path might need adjustment or a more robust path solution.
# For now, using the same path as homepage.py for consistency, assuming 'assets' is in the root.
css_styles = load_css("assets/styles.css")
if css_styles:
    st.markdown(f"<style>{css_styles}</style>", unsafe_allow_html=True)
    # Optional: Add page-specific CSS overrides or additions here if needed
    # For example, to adjust padding for analysis_page specifically:
    st.markdown("""
    <style>
        .main .block-container {
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
    </style>
    """, unsafe_allow_html=True)


# --- Helper Functions for Data Transformation & Display ---

# get_nested_value is now imported from utils

def display_basic_info(customer_data, zh_map):
    """Displays basic customer information in a structured way."""
    st.markdown("<div class='info-card'><h4>👤 基本個人資料</h4>", unsafe_allow_html=True)

    fields_to_display = [
        "customer_id", "name", "gender", "birthdate", "age",
        "occupation", "marital_status", "health_status", "smoking", "property_proof", "希望購買保單"
    ]
    contact_fields = ["contact.phone", "contact.address"]

    for field_key in fields_to_display:
        value = get_nested_value(customer_data, field_key)
        display_name = zh_map.get(field_key, field_key.split('.')[-1].replace("_", " ").title())
        if field_key == "smoking":
            value_display = "🚬 是" if value else "🚭 否"
        else:
            value_display = value
        st.markdown(f"<p><strong>{display_name}:</strong> {value_display}</p>", unsafe_allow_html=True)

    st.markdown("<h5>📞 聯絡資訊</h5>", unsafe_allow_html=True)
    contact_info_available = False
    for field_key in contact_fields:
        value = get_nested_value(customer_data, field_key)
        if value != "N/A":
            contact_info_available = True
            display_name = zh_map.get(field_key, field_key.split('.')[-1].replace("_", " ").title())
            st.markdown(f"<p><strong>{display_name}:</strong> {value}</p>", unsafe_allow_html=True)
    if not contact_info_available:
        st.markdown("<p><i>無聯絡資訊提供</i></p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def display_records(record_data, zh_map):
    """Displays past records in a structured way, using cards or tables."""
    if not record_data:
        st.info("此客戶尚無過往紀錄可供顯示。")
        return

    st.markdown("<div class='info-card'><h4>🗂️ 客戶歷史紀錄</h4>", unsafe_allow_html=True)

    # Credit Rating & Alert
    st.markdown(f"<h5><span style='color:#005A9C;'>💳 信用狀況</span></h5>", unsafe_allow_html=True)
    credit_rating_val = get_nested_value(record_data, 'credit_rating')
    rating_color = {"AAA": "green", "AA": "green", "A": "olive", "BBB": "orange", "BB": "orange", "B": "red", "CCC": "red", "CC": "red", "C": "red" }
    st.markdown(f"<p><strong>{zh_map.get('credit_rating','信用評等')}:</strong> <span style='color:{rating_color.get(credit_rating_val, 'black')}; font-weight:bold;'>{credit_rating_val}</span></p>", unsafe_allow_html=True)

    credit_alert = get_nested_value(record_data, 'credit_alert', {})
    if credit_alert:
        st.markdown(f"<strong>{zh_map.get('credit_alert', '信用警示項目')}:</strong>", unsafe_allow_html=True)
        alert_html = "<ul>"
        has_any_alert_flag = False
        for k, v in credit_alert.items():
            alert_text = zh_map.get(f'credit_alert.{k}', k)
            alert_value_display = ""
            if isinstance(v, bool):
                alert_value_display = '<span style="color:#D32F2F; font-weight:bold;">⚠️ 是</span>' if v else '<span style="color:green;">✅ 否</span>'
                if v: has_any_alert_flag = True
            elif v is not None and isinstance(v, int) and v > 0:
                 alert_value_display = f'<span style="color:#D32F2F; font-weight:bold;">{v}</span>'
                 has_any_alert_flag = True
            elif v is not None:
                alert_value_display = str(v)
            else:
                alert_value_display = "N/A"
            alert_html += f"<li>{alert_text}: {alert_value_display}</li>"

        if not credit_alert:
             alert_html += "<li>無相關警示資訊</li>"
        elif not has_any_alert_flag and any(isinstance(val, bool) for val in credit_alert.values()):
             alert_html += "<li>✅ 無警示項目觸發</li>"
        alert_html += "</ul>"
        st.markdown(alert_html, unsafe_allow_html=True)
    else:
        st.markdown(f"<p>{zh_map.get('credit_alert', '信用警示項目')}: <i>無資料</i></p>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 0.8rem 0;'>", unsafe_allow_html=True)

    # Insurance History
    insurance_history = get_nested_value(record_data, 'insurance_history', [])
    if insurance_history:
        st.markdown(f"<h5><span style='color:#005A9C;'>📜 保單歷史</span></h5>", unsafe_allow_html=True)
        try:
            df_ins = pd.DataFrame(insurance_history)
            if not df_ins.empty:
                df_ins.columns = [zh_map.get(f'insurance_history.{col}', col) for col in df_ins.columns]
                st.table(df_ins)
            else:
                st.markdown("<p><i>無保單歷史資料。</i></p>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"保單歷史表格轉換失敗: {e}")
            st.json(insurance_history)
        st.markdown("<hr style='margin: 0.8rem 0;'>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h5><span style='color:#005A9C;'>📜 保單歷史</span></h5><p><i>無資料</i></p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0.8rem 0;'>", unsafe_allow_html=True)

    # Claim Records
    claim_records = get_nested_value(record_data, 'claim_records', [])
    if claim_records:
        st.markdown(f"<h5><span style='color:#005A9C;'>賠償紀錄</span></h5>", unsafe_allow_html=True) # Corrected title
        try:
            df_claims = pd.DataFrame(claim_records)
            if not df_claims.empty:
                df_claims.columns = [zh_map.get(f'claim_records.{col}', col) for col in df_claims.columns]
                st.table(df_claims)
            else:
                st.markdown("<p><i>無歷史理賠紀錄。</i></p>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"理賠紀錄表格轉換失敗: {e}")
            st.json(claim_records)
        st.markdown("<hr style='margin: 0.8rem 0;'>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h5><span style='color:#005A9C;'>賠償紀錄</span></h5><p><i>無資料</i></p>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 0.8rem 0;'>", unsafe_allow_html=True)

    # Other records
    st.markdown(f"<h5><span style='color:#005A9C;'>其他重要紀錄</span></h5>", unsafe_allow_html=True)
    simple_records_map = {
        'review_records': '⚖️ 審查紀錄',
        'suspicious_transaction': 'ธุรก 可疑交易', # Replaced icon for better compatibility
        'criminal_record': '📜 刑事紀錄'
    }
    for rec_key, title_with_icon in simple_records_map.items():
        data = get_nested_value(record_data, rec_key, {})
        title_display = zh_map.get(rec_key, title_with_icon.split(" ",1)[1] if " " in title_with_icon else title_with_icon) # Get original title if not in zh_map
        icon = title_with_icon.split(" ",1)[0] if " " in title_with_icon else ""

        st.markdown(f"<strong>{icon} {title_display}:</strong>", unsafe_allow_html=True)
        if data:
            rec_html = "<ul>"
            item_displayed = False
            for k, v in data.items():
                item_key_display = zh_map.get(f'{rec_key}.{k}', k)
                item_value_display = ""
                if isinstance(v, bool):
                    item_value_display = '<span style="color:#D32F2F; font-weight:bold;">⚠️ 是</span>' if v else '<span style="color:green;">✅ 否</span>'
                elif v is not None:
                    item_value_display = str(v)
                else: # Should be caught by get_nested_value default, but as a fallback
                    item_value_display = "N/A"
                rec_html += f"<li>{item_key_display}: {item_value_display}</li>"
                item_displayed = True
            if not item_displayed: # If data dict was not empty but contained no actual items for display
                 rec_html += "<li><i>無相關子項目資訊</i></li>"
            rec_html += "</ul>"
            st.markdown(rec_html, unsafe_allow_html=True)
        else: # Data dict itself is empty or N/A
            st.markdown("<p><i>無資料</i></p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True) # Add a bit of space

    current_assets = get_nested_value(record_data, 'current_assets', [])
    st.markdown(f"<strong>💰 現有資產:</strong>", unsafe_allow_html=True)
    if current_assets:
        st.markdown(f"<p>{', '.join(current_assets)}</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p><i>無資料</i></p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# --- Utility Functions from config_rules ---
# get_class_desc_map, get_rule_class_map, get_rule_required_map are now imported from utils

# --- Load Data ---
@st.cache_data
def load_data():
    # Determine base path for data files, works if pages script is in 'pages' subdir
    base_path = os.path.join(os.path.dirname(__file__), "..")
    basic_info_path = os.path.join(base_path, "客戶基本資訊/基本資訊.json")
    records_path = os.path.join(base_path, "客戶過往紀錄/過往紀錄.json")

    try:
        with open(basic_info_path, "r", encoding="utf-8") as f:
            customers_list = json.load(f)
        with open(records_path, "r", encoding="utf-8") as f:
            records_list = json.load(f)
    except FileNotFoundError:
        st.error(f"錯誤：找不到客戶資料檔案。預期路徑: {basic_info_path}, {records_path}。請確認檔案路徑是否正確。")
        return [], {}, {}
    except json.JSONDecodeError:
        st.error("錯誤：客戶資料檔案格式錯誤，無法解析 JSON。")
        return [], {}, {}
    customer_map = {c.get("name"): c for c in customers_list if c.get("name")}
    id_to_record_map = {r.get("customer_id"): r for r in records_list if r.get("customer_id")}
    return customers_list, customer_map, id_to_record_map

customers, customer_dict, id_to_record = load_data()

# --- Main Application UI ---
st.markdown("<h1 style='text-align: center; color: #003366;'>智慧承保風險評估</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #4B5563; margin-bottom: 2rem;'><i>選擇客戶以載入資料並執行 AI 風險分析</i></p>", unsafe_allow_html=True)


if not customers:
    st.warning("無法載入客戶列表。請檢查資料檔案。")
    st.stop()

names = [""] + [c["name"] for c in customers if c.get("name")]
if len(names) == 1: # Only blank option
    st.warning("客戶名單中沒有有效的客戶名稱可供選擇。")
    st.stop()

selected_name = st.selectbox(" STEP 1 : 👤 請選擇客戶姓名進行分析", names, index=0, help="從列表中選擇一位客戶以載入其詳細資料和過往紀錄。")

if selected_name and selected_name in customer_dict:
    customer = customer_dict[selected_name]
    record = id_to_record.get(customer.get("customer_id"))

    st.markdown(f"<h2 style='color: #005A9C; border-bottom: 2px solid #005A9C; padding-bottom: 0.5rem;'>📈 客戶風險總覽：{selected_name}</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True) # Add some space

    # Customer Dashboard Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="🆔 客戶ID", value=customer.get("customer_id", "N/A"))
    with col2:
        st.metric(label="🎂 年齡", value=f"{customer.get('age', 'N/A')} 歲")
    with col3:
        credit_rating_val = get_nested_value(record, "credit_rating", "N/A")
        st.metric(label="🌟 信用評等", value=credit_rating_val)
    with col4:
        has_credit_alert = False
        credit_alert_data = get_nested_value(record, "credit_alert", {})
        if isinstance(credit_alert_data, dict):
            if any(v for k, v in credit_alert_data.items() if isinstance(v, bool) and k != 'placeholder_for_no_alerts'):
                has_credit_alert = True
            elif any(v > 0 for k, v in credit_alert_data.items() if isinstance(v, int) and "count" in k.lower()):
                has_credit_alert = True
        st.metric(label="🚨 信用警示", value="⚠️ 有" if has_credit_alert else "✅ 無", help="檢查是否有信用卡逾期、呆帳等警示。")

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True) # Spacer

    # Expander for Basic Info and Records
    st.markdown('<div class="expander-styling">', unsafe_allow_html=True)
    with st.expander("👤 詳細基本資料", expanded=False): # Default to not expanded
        display_basic_info(customer, all_field_zh)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="expander-styling">', unsafe_allow_html=True)
    with st.expander("🗂️ 詳細過往紀錄", expanded=False): # Default to not expanded
        if record:
            display_records(record, all_field_zh)
        else:
            st.info("此客戶尚無過往紀錄可供顯示。")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color: #005A9C; border-bottom: 2px solid #005A9C; padding-bottom: 0.5rem;'>🧠 STEP 2 : AI 智能承保分析</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    ai_col1, ai_col2 = st.columns([2,1]) # Ratio for description and button
    with ai_col1:
        st.markdown("""
        <div class='info-card' style='background-color: #E9F5FF; border-left-color: #007BFF;'>
            <h5 style='color:#0056B3'>🤖 AI 分析引擎</h5>
            <p>點擊右側「執行 AI 分析」按鈕，系統將整合客戶的全面數據，運用先進的 AI 模型進行深度風險評估。模型將依據預設的承保規則庫（如財產保險、醫療險、壽險等）進行分析，並生成詳細的風險報告。</p>
            <p style='font-size:0.9em; color:#555;'><i>若該客戶已有分析結果，您也可以直接點選下方按鈕查看歷史報告。</i></p>
        </div>
        """, unsafe_allow_html=True)

    with ai_col2:
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True) # Spacer for button alignment
        if "ai_analysis_triggered_for" not in st.session_state:
            st.session_state.ai_analysis_triggered_for = None
        if "show_ai_result_for" not in st.session_state:
            st.session_state.show_ai_result_for = None

        if st.button("🚀 執行 AI 分析", key=f"exec_ai_{customer.get('customer_id')}", use_container_width=True, help="開始對此客戶進行 AI 承保風險分析。"):
            st.session_state.ai_analysis_triggered_for = customer.get('customer_id')
            st.session_state.show_ai_result_for = None
            with st.spinner(f"對客戶 {selected_name} 的 AI 分析進行中，請稍候..."):
                customer_data_for_api = customer.copy()
                if record:
                    for k, v in record.items():
                        if k != "customer_id": customer_data_for_api[k] = v

                # Determine base path for results, works if pages script is in 'pages' subdir
                results_base_path = os.path.join(os.path.dirname(__file__), "..", "Results")
                if not os.path.exists(results_base_path):
                    os.makedirs(results_base_path) # Create Results dir if it doesn't exist

                api_result = call_agent_api(customer_data_for_api, config_rules.config_rules)
                if api_result:
                    final_result_data = extract_final_results(api_result)
                    if final_result_data:
                        # Ensure Results directory exists (relative to the main script, Home.py)
                        # This save_results call assumes agent_api_client.py handles path correctly,
                        # or that 'Results' is in the same dir as Home.py or an absolute path is used internally.
                        # For multi-page apps, file paths can be tricky.
                        # Assuming save_results in agent_api_client.py writes to a 'Results' dir in the root.
                        results_dir_in_root = os.path.join(os.path.dirname(__file__), "..", "Results")
                        if not os.path.exists(results_dir_in_root):
                            try:
                                os.makedirs(results_dir_in_root)
                            except OSError as e:
                                st.error(f"無法創建 Results 資料夾於 {results_dir_in_root}: {e}")
                                # Optionally, you might want to stop or handle this error differently

                        # Call save_results WITHOUT base_path_override
                        save_results(final_result_data, customer["customer_id"])
                        st.session_state.show_ai_result_for = customer.get('customer_id')
                        st.success(f"✅ AI 分析已為客戶 {selected_name} 完成並儲存結果！")
                    else: st.error("⚠️ AI 回傳內容解析失敗。")
                else: st.error("❌ API 呼叫失敗。")
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True) # Spacer for button alignment

    # Path to results, assuming 'Results' is in the root directory relative to where Home.py is run
    # This needs to be relative to the location of THIS script (analysis_page.py) to find the root
    results_dir_relative_to_root = os.path.join(os.path.dirname(__file__), "..", "Results")
    result_path = os.path.join(results_dir_relative_to_root, f"result_{customer.get('customer_id')}.json")
    ai_result_exists = os.path.exists(result_path)

    if ai_result_exists and st.session_state.show_ai_result_for != customer.get('customer_id'):
        if st.button(f"📜 顯示 {selected_name} 的歷史 AI 分析結果", key=f"show_hist_ai_{customer.get('customer_id')}", use_container_width=True):
            st.session_state.show_ai_result_for = customer.get('customer_id')

    if st.session_state.show_ai_result_for == customer.get('customer_id'):
        if ai_result_exists:
            with open(result_path, "r", encoding="utf-8") as f:
                ai_result = json.load(f)

            st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: #005A9C;'>📄 AI 分析結果報告：{selected_name}</h3>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            sc_col1, sc_col2 = st.columns(2)
            with sc_col1:
                st.markdown(f"<div class='info-card' style='background-color: #E9F5FF; text-align:center;'><h5 style='margin-bottom:0.3rem;'>綜合評估總分</h5><p style='font-size:2.5em; font-weight:bold; color:#005A9C; margin-bottom:0;'>{ai_result.get('total_score', 'N/A')}</p></div>", unsafe_allow_html=True)
            with sc_col2:
                grade = ai_result.get('grade', 'N/A')
                grade_color_map = {"A+": "#28A745", "A": "#28A745", "B": "#FFC107", "C": "#DC3545", "D": "#DC3545"}
                grade_text_map = {"A+": "優良", "A": "良好", "B": "中等", "C": "警示", "D": "高風險"}
                st.markdown(f"<div class='info-card' style='background-color: {grade_color_map.get(grade, '#F8F9FA')}20; text-align:center;'><h5 style='margin-bottom:0.3rem;'>風險評級</h5><p style='font-size:2.5em; font-weight:bold; color:{grade_color_map.get(grade, '#6C757D')}; margin-bottom:0;'>{grade} <span style='font-size:0.6em; vertical-align:middle;'>({grade_text_map.get(grade, '未知')})</span></p></div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("<h5>📊 分數評級區間參考</h5>", unsafe_allow_html=True)
            score_colors_bg = {"A+": "#D4EDDA", "A": "#CFE2FF", "B": "#FFF3CD", "C": "#F8D7DA", "D": "#E9ECEF"}
            score_colors_text = {"A+": "#155724", "A": "#004085", "B": "#856404", "C": "#721C24", "D": "#383D41"}
            score_ranges = {"A+": "65～70分", "A": "55～64分", "B": "45～54分", "C": "40～44分", "D":"39分以下"}

            html_score_table = "<table class='score-range-table'><thead><tr>"
            for grade_key in score_ranges.keys():
                html_score_table += f"<th style='background-color:{score_colors_bg.get(grade_key, '#F8F9FA')}; color:{score_colors_text.get(grade_key, '#212529')};'>{grade_key}</th>"
            html_score_table += "</tr></thead><tbody><tr>"
            for grade_key, range_val in score_ranges.items():
                html_score_table += f"<td>{range_val}</td>"
            html_score_table += "</tr></tbody></table>"
            st.markdown(html_score_table, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("<h5>📜 規則合規詳細情況</h5>", unsafe_allow_html=True)
            try:
                rule_class_map = get_rule_class_map()
                rule_required_map = get_rule_required_map()
                class_desc_map = get_class_desc_map()
            except Exception as e:
                st.error(f"載入規則對照表時發生錯誤: {e}")
                rule_class_map, rule_required_map, class_desc_map = {}, {}, {}

            score_table_data = ai_result.get("score_table", [])
            if score_table_data:
                # --- Start: AI Compliance Table using external CSS ---
                table_data_compliance = []
                rule_explain_map_compliance = {item.get("項目", ""): item.get("規則", "") for item in score_table_data}

                for item in score_table_data:
                    keyword = item.get("項目", "")
                    required_compliance = rule_required_map.get(keyword, "○ 選擇") # Assumes rule_required_map is available
                    table_data_compliance.append({
                        "分數": item.get("分數", ""),
                        "規則名稱": keyword,
                        "規則名稱顯示": all_field_zh.get(keyword, keyword),
                        "必要性": required_compliance,
                        "類別": rule_class_map.get(keyword, "未知") # Assumes rule_class_map is available
                    })

                grouped_compliance = OrderedDict()
                for row_compliance in table_data_compliance:
                    grouped_compliance.setdefault(row_compliance["類別"], []).append(row_compliance)

                # Class colors can still be defined here for dynamic background if needed,
                # or managed by CSS if classes are added to rows/cells.
                # For simplicity, keeping Python-driven background for category cells for now.
                class_colors_compliance = ["#e6f2ff", "#f9f9d1", "#e8f6e8", "#ffe6e6", "#f3e6ff", "#fff2cc"]
                class_color_map_compliance = {}
                for idx, k_compliance in enumerate(grouped_compliance.keys()):
                    class_color_map_compliance[k_compliance] = class_colors_compliance[idx % len(class_colors_compliance)]

                def beautify_rule_desc_html_compliance(desc_str):
                    import re
                    items = re.split(r'[；;\n]+', desc_str)
                    items = [i.strip() for i in items if i.strip()]
                    html_list_items = []
                    for item_text in items:
                        if '：' in item_text:
                            k_part, v_part = item_text.split('：', 1)
                            v_part = v_part.strip()
                            if not v_part.endswith('分'):
                                v_part = v_part + '分'
                            html_list_items.append(f'<li>📊 <b>{k_part}</b>：<span style="color:#1a5fb4;font-weight:bold">{v_part}</span></li>')
                        elif ':' in item_text: # Fallback
                            k_part, v_part = item_text.split(':', 1)
                            v_part = v_part.strip()
                            if not v_part.endswith('分'):
                                v_part = v_part + '分'
                            html_list_items.append(f'<li>📊 <b>{k_part}</b>：<span style="color:#1a5fb4;font-weight:bold">{v_part}</span></li>')
                        else:
                            html_list_items.append(f'<li>{item_text}</li>')
                    return '<ul style="margin:0 0 0 1em;padding:0;list-style:none;text-align:left;">' + ''.join(html_list_items) + '</ul>' if html_list_items else desc_str

                # HTML for the table, referencing '.ai-compliance-table' and its sub-classes from styles.css
                # No <style> block here.
                html_compliance_table = f'''
                <div>
                    <table class="ai-compliance-table">
                        <thead>
                            <tr><th>分數</th><th>規則名稱</th><th>必要性</th><th>類別</th></tr>
                        </thead>
                        <tbody>
                '''
                for cls_compliance, rows_compliance in grouped_compliance.items():
                    rowspan_compliance = len(rows_compliance)
                    # Background color for category cell still applied inline, can be moved to CSS if preferred
                    # by adding dynamic classes like class-{cls_compliance_sanitized_name}
                    category_bg_color = class_color_map_compliance.get(cls_compliance, "#FFFFFF")

                    for i_compliance, row_item_compliance in enumerate(rows_compliance):
                        html_compliance_table += "<tr>"
                        html_compliance_table += f"<td>{row_item_compliance['分數']}</td>"

                        rule_key_compliance = row_item_compliance['規則名稱']
                        rule_desc_compliance = rule_explain_map_compliance.get(rule_key_compliance, '')
                        beautified_desc_compliance = beautify_rule_desc_html_compliance(rule_desc_compliance)

                        html_compliance_table += f"<td><span class='rule-link'>{row_item_compliance['規則名稱顯示']}<span class='rule-tooltip'>{beautified_desc_compliance}</span></span></td>"
                        html_compliance_table += f"<td>{row_item_compliance['必要性']}</td>"

                        if i_compliance == 0:
                            desc_cls_compliance = class_desc_map.get(cls_compliance, "") # Assumes class_desc_map available
                            # Inline style for background-color retained for dynamic category colors.
                            # Other styles for .class-cell (cursor, position, font-weight, min-width) are in CSS.
                            html_compliance_table += f"<td rowspan='{rowspan_compliance}' class='class-cell' style='background-color:{category_bg_color};'>"
                            html_compliance_table += f"{cls_compliance}"
                            if desc_cls_compliance:
                                html_compliance_table += f"<span class='class-tooltip'><b>📂 {cls_compliance}</b><br>{desc_cls_compliance}</span>"
                            html_compliance_table += "</td>"
                        html_compliance_table += "</tr>"
                html_compliance_table += "</tbody></table></div>"

                components.html(html_compliance_table, height=max(450, len(table_data_compliance) * 50 + len(grouped_compliance) * 25), scrolling=True)
                # --- End: AI Compliance Table ---
            else:
                st.info("AI分析結果中未包含詳細的規則分數表。")

            st.markdown("<div style='margin-top: 1.5rem; margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True) # Adjusted spacing

            st.markdown("<h5>🧑‍⚖️ 專家洞察與建議</h5>", unsafe_allow_html=True)
            # Removed the negative margin div, will control spacing with card margins or specific spacers if needed.


            summary_cols = st.columns(2, gap="large")
            with summary_cols[0]:
                st.markdown(f"""
                <div class='info-card' style='height:100%; border-left-color:#28A745; margin-top:0.5rem;'>
                    <h6 style='color:#28A745; display:flex; align-items:center; margin-bottom: 0.6rem; font-size:1.35em;'>
                        <span style='font-size:1.7em; margin-right:0.5em;'>👍</span> 優點
                    </h6>
                """, unsafe_allow_html=True)
                advantages = ai_result.get('優點', [])
                if advantages:
                    for adv in advantages: st.markdown(f"<p style='font-size:0.9em; margin-bottom:0.2rem;'>• {adv}</p>", unsafe_allow_html=True)
                else: st.markdown("<p style='font-size:0.9em;'><i>暫無記錄</i></p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with summary_cols[1]:
                st.markdown(f"""
                <div class='info-card' style='height:100%; border-left-color:#DC3545; margin-top:0.5rem;'>
                    <h6 style='color:#DC3545; display:flex; align-items:center; margin-bottom: 0.6rem; font-size:1.35em;'>
                        <span style='font-size:1.7em; margin-right:0.5em;'>👎</span> 風險
                    </h6>
                """, unsafe_allow_html=True)
                risks = ai_result.get('風險', [])
                if risks:
                    for risk_item in risks: st.markdown(f"<p style='font-size:0.9em; margin-bottom:0.2rem;'>• {risk_item}</p>", unsafe_allow_html=True)
                else: st.markdown("<p style='font-size:0.9em;'><i>暫無記錄</i></p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(f"""
            <div class='info-card' style='border-left-color:#007BFF; margin-top:1rem;'>
                <h6 style='color:#007BFF; display:flex; align-items:center; margin-bottom: 0.6rem; font-size:1.35em;'>
                    <span style='font-size:1.7em; margin-right:0.5em;'>📝</span> 建議
                </h6>
            """, unsafe_allow_html=True)
            suggestions = ai_result.get('建議', [])
            if suggestions:
                for sug in suggestions: st.markdown(f"<p style='font-size:0.9em; margin-bottom:0.2rem;'>• {sug}</p>", unsafe_allow_html=True)
            else: st.markdown("<p style='font-size:0.9em;'><i>暫無記錄</i></p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"""
            <div class='info-card' style='background-color:#F8F9FA; border-left-color:#6F42C1; margin-top:1rem;'>
                <h6 style='color:#6F42C1; display:flex; align-items:center; margin-bottom: 0.6rem; font-size:1.35em;'>
                    <span style='font-size:1.7em; margin-right:0.5em;'>🧐</span> 專家綜合說明
                </h6>
            """, unsafe_allow_html=True)
            expert_summary = ai_result.get('專家綜合說明', '無相關綜合說明。')
            st.markdown(f"<p style='font-size:0.95em; line-height:1.6;'>{expert_summary}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.ai_analysis_triggered_for == customer.get('customer_id'):
             st.warning(f"AI 分析結果檔案 ({result_path}) 未找到，但分析流程已執行。請確認檔案儲存路徑或稍後再試。")
elif names and "" in names and len(names) > 1 and not selected_name :
    st.info("👈 請從上方下拉選單中選擇一位客戶以開始分析。")

st.markdown("<hr style='margin: 3rem 0 1rem 0;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color: #6C757D; font-size:0.9em;'>© 2024 智慧承保風險評估平台</p>", unsafe_allow_html=True)
