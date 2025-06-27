
# 匯入套件與對應表
import streamlit as st
import json
import os
from agent_api_client import call_agent_api, extract_final_results, save_results
import config_rules
from 中文規則對應 import all_field_zh

# 工具函式
def get_class_desc_map():
    # 建立 類別 -> 描述 對照表
    class_desc_map = {}
    for rule_group in config_rules.config_rules.values():
        for rule in rule_group:
            class_desc_map[rule["class"]] = rule.get("description", "")
    return class_desc_map

def get_rule_class_map():
    # 建立 項目 -> 類別 對照表
    rule_class_map = {}
    for rule_group in config_rules.config_rules.values():
        for rule in rule_group:
            for kw in rule["keywords"]:
                rule_class_map[kw] = rule["class"]
    return rule_class_map

def get_rule_required_map():
    # 建立 項目 -> 必要性 對照表
    rule_required_map = {}
    for rule_group in config_rules.config_rules.values():
        for rule in rule_group:
            for kw in rule["keywords"]:
                rule_required_map[kw] = "必要" if rule.get("required", False) else "選擇"
    return rule_required_map

def get_rule_name_map():
    # 建立 項目 -> 規則中文名稱 對照表
    rule_name_map = {}
    for rule_group in config_rules.config_rules.values():
        for rule in rule_group:
            for kw in rule["keywords"]:
                rule_name_map[kw] = rule["rule"]
    return rule_name_map

# 讀取基本資料
with open("客戶基本資訊/基本資訊.json", "r", encoding="utf-8") as f:
    customers = json.load(f)

# 讀取過往紀錄
with open("客戶過往紀錄/過往紀錄.json", "r", encoding="utf-8") as f:
    records = json.load(f)

customer_dict = {c["name"]: c for c in customers}
id_to_record = {r["customer_id"]: r for r in records}

st.title("客戶資料查詢")

names = [c["name"] for c in customers]
selected_name = st.selectbox("請選擇客戶姓名", names)

if selected_name:
    customer = customer_dict[selected_name]
    st.subheader("基本資料")
    # 轉換基本資料為中文欄位
    zh_customer = {all_field_zh.get(k, k): v for k, v in customer.items()}
    # 處理 contact 巢狀欄位
    if "contact" in customer and isinstance(customer["contact"], dict):
        zh_customer_contact = {all_field_zh.get(f"contact.{k}", k): v for k, v in customer["contact"].items()}
        zh_customer[all_field_zh.get("contact", "聯絡資訊")] = zh_customer_contact
        # 若原本有英文 contact key，移除
        if "contact" in zh_customer:
            del zh_customer["contact"]
    st.json(zh_customer)

    record = id_to_record.get(customer["customer_id"])
    if st.button("查詢過往紀錄"):
        if record:
            st.subheader("過往紀錄")
            # 信用評等
            st.write(f"{all_field_zh.get('credit_rating','信用評等')}：{record.get('credit_rating','')}")
            # 信用警示
            st.write(all_field_zh.get('credit_alert', '信用警示') + "：")
            zh_credit_alert = {all_field_zh.get(f"credit_alert.{k}", k): v for k, v in record.get("credit_alert", {}).items()}
            st.json(zh_credit_alert)
            # 保單歷史
            st.write(all_field_zh.get('insurance_history', '保單歷史') + "：")
            zh_insurance_history = [
                {all_field_zh.get(f"insurance_history.{k}", k): v for k, v in item.items()}
                for item in record.get("insurance_history", [])
            ]
            st.table(zh_insurance_history)
            # 理賠紀錄
            st.write(all_field_zh.get('claim_records', '理賠紀錄') + "：")
            zh_claim_records = [
                {all_field_zh.get(f"claim_records.{k}", k): v for k, v in item.items()}
                for item in record.get("claim_records", [])
            ]
            st.table(zh_claim_records)
            # 審查紀錄
            st.write(all_field_zh.get('review_records', '審查紀錄') + "：")
            zh_review_records = {all_field_zh.get(f"review_records.{k}", k): v for k, v in record.get("review_records", {}).items()}
            st.json(zh_review_records)
            # 可疑交易
            st.write(all_field_zh.get('suspicious_transaction', '可疑交易') + "：")
            zh_suspicious_transaction = {all_field_zh.get(f"suspicious_transaction.{k}", k): v for k, v in record.get("suspicious_transaction", {}).items()}
            st.json(zh_suspicious_transaction)
            # 刑事紀錄
            st.write(all_field_zh.get('criminal_record', '刑事紀錄') + "：")
            zh_criminal_record = {all_field_zh.get(f"criminal_record.{k}", k): v for k, v in record.get("criminal_record", {}).items()}
            st.json(zh_criminal_record)
            # 現有資產
            st.write(all_field_zh.get('current_assets', '現有資產') + "：" + "，".join(record.get("current_assets", [])))
        else:
            st.warning("查無過往紀錄。")

    # 智慧分析承保 Agent 按鈕
    if st.button("智慧分析承保 Agent"):
        # 合併基本資料與過往紀錄
        customer_data = customer.copy()
        if record:
            for k, v in record.items():
                if k != "customer_id":
                    customer_data[k] = v
        # 呼叫 API 並儲存
        result = call_agent_api(customer_data, config_rules.config_rules)
        if result:
            final_result = extract_final_results(result)
            if final_result:
                save_results(final_result, customer["customer_id"])
                st.success("AI 分析已完成並儲存！")
            else:
                st.error("AI 回傳內容解析失敗")
        else:
            st.error("API 呼叫失敗")

    # 僅在按下按鈕後顯示 AI 分析結果
    if "show_ai_result" not in st.session_state:
        st.session_state["show_ai_result"] = False

    if st.button("顯示 AI 智慧分析結果"):
        st.session_state["show_ai_result"] = True

    if st.session_state["show_ai_result"]:
        import streamlit.components.v1 as components
        result_path = f"Results/result_{customer['customer_id']}.json"
        if os.path.exists(result_path):
            with open(result_path, "r", encoding="utf-8") as f:
                ai_result = json.load(f)

            # 分數評級區塊
            st.markdown("""
<div style='display:flex;gap:32px;align-items:center;margin-bottom:12px;'>
  <div style='flex:1;text-align:center;'>
    <div style='font-size:52px;font-weight:bold;color:#1a5fb4'>{}</div>
    <div style='font-size:18px;color:#555;'>總分</div>
  </div>
  <div style='flex:1;text-align:center;'>
    <div style='font-size:52px;font-weight:bold;color:#e67e22'>{}</div>
    <div style='font-size:18px;color:#555;'>評級</div>
  </div>
</div>
""".format(ai_result['total_score'], ai_result['grade']), unsafe_allow_html=True)

            # 分數區間表（自訂 HTML，A+/A/B/C 不同底色）
            score_colors = {
                "A+": "#e6f2ff",
                "A": "#e8f6e8",
                "B": "#fff2cc",
                "C": "#ffe6e6"
            }
            html_score = '''<style>
            .score-range-table th, .score-range-table td { border:1.5px solid #bbb; padding:10px 0; text-align:center; font-size:20px; }
            .score-range-table th { background:#2c5c88; color:#fff; }
            </style>
            <table class="score-range-table" style="border-collapse:collapse;width:100%;margin-bottom:24px;">
            <tr>'''
            for k in ["A+", "A", "B", "C"]:
                html_score += f'<th style="background:{score_colors[k]};color:#222;">{k}</th>'
            html_score += '</tr><tr>'
            for k in ["A+", "A", "B", "C"]:
                html_score += f'<td style="background:{score_colors[k]};color:#222;font-size:18px;">'
                if k == "A+":
                    html_score += "65～70分"
                elif k == "A":
                    html_score += "55～64分"
                elif k == "B":
                    html_score += "45～54分"
                elif k == "C":
                    html_score += "44分以下"
                html_score += '</td>'
            html_score += '</tr></table>'
            components.html(html_score, height=100)

            # 規則合規情況表格（無標題，直接顯示）
            # 產生 HTML 表格，規則名稱 hover 顯示規則說明
            from collections import OrderedDict
            rule_class_map = get_rule_class_map()
            rule_required_map = get_rule_required_map()
            class_desc_map = get_class_desc_map()
            table_data = []
            rule_explain_map = {item.get("項目", ""): item.get("規則", "") for item in ai_result.get("score_table", [])}
            for item in ai_result.get("score_table", []):
                keyword = item.get("項目", "")
                required = rule_required_map.get(keyword, "選擇")
                if required == "必要":
                    required_str = "✦ 必要"
                else:
                    required_str = "○ 選擇"
                table_data.append({
                    "分數": item.get("分數", ""),
                    "規則名稱": keyword,
                    "規則名稱顯示": all_field_zh.get(keyword, keyword),
                    "必要性": required_str,
                    "類別": rule_class_map.get(keyword, "未知")
                })
            grouped = OrderedDict()
            for row in table_data:
                grouped.setdefault(row["類別"], []).append(row)
            class_colors = ["#e6f2ff", "#f9f9d1", "#e8f6e8", "#ffe6e6", "#f3e6ff", "#fff2cc"]
            class_color_map = {}
            for idx, k in enumerate(grouped.keys()):
                class_color_map[k] = class_colors[idx % len(class_colors)]
            html = '''<style>
            .score-table th, .score-table td { border:1px solid #bbb; border-bottom:3.5px solid #2c5c88; padding:8px 12px; text-align:center; font-size:16px; }
            .score-table th { background:#2c5c88; color:#fff; }
            .score-table .class-cell { cursor: pointer; position:relative; }
            .class-tooltip { display:none; position:absolute; left:100%; top:50%; transform:translateY(-50%); background:#fff; color:#222; border:1.5px solid #2c5c88; border-radius:10px; padding:16px 28px; min-width:260px; max-width:480px; box-shadow:0 4px 16px #888; z-index:99999; font-size:16px; text-align:left; white-space:pre-line; word-break:break-all; }
            .class-cell:hover .class-tooltip { display:block; }
            .score-table .rule-link { color: #222; text-decoration: none; cursor: default; position:relative; }
            .score-table td { background:#fff; }
            .rule-tooltip { display:none; position:absolute; left:100%; top:50%; transform:translateY(-50%); background:#fff; color:#222; border:1.5px solid #1a5fb4; border-radius:8px; padding:10px 16px; min-width:180px; max-width:320px; box-shadow:0 2px 8px #888; z-index:9999; font-size:15px; white-space:pre-line; }
            .rule-link:hover .rule-tooltip { display:block; }
            </style>
            <div><table class="score-table" style="border-collapse:collapse;width:100%;min-width:600px;">
            <tr><th>分數</th><th>規則名稱</th><th>必要性</th><th>類別</th></tr>
            '''
            for idx, (cls, rows) in enumerate(grouped.items()):
                rowspan = len(rows)
                color = class_color_map[cls]
                for i, row in enumerate(rows):
                    html += "<tr>"
                    html += f"<td>{row['分數']}</td>"
                    rule_key = row['規則名稱']
                    rule_desc = rule_explain_map.get(rule_key, '')
                    def beautify_rule_desc(desc):
                        import re
                        items = re.split(r'[；;\n]+', desc)
                        items = [i.strip() for i in items if i.strip()]
                        html_list = []
                        for item in items:
                            if '：' in item:
                                k, v = item.split('：', 1)
                                v = v.strip()
                                if not v.endswith('分'):
                                    v = v + '分'
                                html_list.append(f'<li>📊 <b>{k}</b>：<span style="color:#1a5fb4;font-weight:bold">{v}</span></li>')
                            elif ':' in item:
                                k, v = item.split(':', 1)
                                v = v.strip()
                                if not v.endswith('分'):
                                    v = v + '分'
                                html_list.append(f'<li>📊 <b>{k}</b>：<span style="color:#1a5fb4;font-weight:bold">{v}</span></li>')
                            else:
                                html_list.append(f'<li>{item}</li>')
                        return '<ul style="margin:0 0 0 1em;padding:0;list-style:none;text-align:left;">' + ''.join(html_list) + '</ul>' if html_list else desc
                    beautified = beautify_rule_desc(rule_desc)
                    html += f"<td><span class='rule-link'>{row['規則名稱顯示']}<span class='rule-tooltip'>{beautified}</span></span></td>"
                    html += f"<td>{row['必要性']}</td>"
                    if i == 0:
                        desc = class_desc_map.get(cls, "")
                        html += f"<td rowspan='{rowspan}' class='class-cell' style='background:{color};font-weight:bold;min-width:90px;position:relative;'>{cls}"
                        if desc:
                            html += f"<span class='class-tooltip'><b>📂 {cls}</b><br>{desc}</span>"
                        html += "</td>"
                    html += "</tr>"
            html += "</table></div>"

            st.markdown("#### 規則合規情況")
            components.html(html, height=800, scrolling=False)

            # 優點、風險、建議、專家綜合說明區塊（移到規則合規情況表格下方）
            st.markdown("""
<div style='display:flex;gap:32px;margin-top:48px;'>
  <div style='flex:1;'>
    <div style='font-size:20px;font-weight:bold;color:#388e3c;margin-bottom:6px;'>優點</div>
    <ul style='margin:0 0 18px 1.2em;padding:0;color:#222;'>
      {}
    </ul>
    <div style='font-size:20px;font-weight:bold;color:#c0392b;margin-bottom:6px;'>風險</div>
    <ul style='margin:0 0 18px 1.2em;padding:0;color:#222;'>
      {}
    </ul>
    <div style='font-size:20px;font-weight:bold;color:#1a5fb4;margin-bottom:6px;'>建議</div>
    <ul style='margin:0 0 18px 1.2em;padding:0;color:#222;'>
      {}
    </ul>
  </div>
  <div style='flex:1;'>
    <div style='font-size:20px;font-weight:bold;color:#8e44ad;margin-bottom:6px;'>專家綜合說明</div>
    <div style='background:#f6f6fa;border-left:5px solid #8e44ad;padding:18px 20px 18px 18px;border-radius:8px;color:#333;font-size:17px;'>
      {}
    </div>
  </div>
</div>
""".format(
    '\n'.join([f'<li>{adv}</li>' for adv in ai_result.get('優點', [])]) or '<li>無</li>',
    '\n'.join([f'<li>{risk}</li>' for risk in ai_result.get('風險', [])]) or '<li>無</li>',
    '\n'.join([f'<li>{sug}</li>' for sug in ai_result.get('建議', [])]) or '<li>無</li>',
    ai_result.get('專家綜合說明', '')
), unsafe_allow_html=True)


            # 細項分數表格
            rule_class_map = get_rule_class_map()
            rule_required_map = get_rule_required_map()
            class_desc_map = get_class_desc_map()
            # 對話框狀態
            if "rule_dialog" not in st.session_state:
                st.session_state["rule_dialog"] = None
            # 準備分數細項資料
            table_data = []
            rule_explain_map = {item.get("項目", ""): item.get("規則", "") for item in ai_result.get("score_table", [])}
            for item in ai_result.get("score_table", []):
                keyword = item.get("項目", "")
                required = rule_required_map.get(keyword, "選擇")
                if required == "必要":
                    required_str = "✦ 必要"
                else:
                    required_str = "○ 選擇"
                table_data.append({
                    "分數": item.get("分數", ""),
                    "規則名稱": keyword,
                    "規則名稱顯示": all_field_zh.get(keyword, keyword),
                    "必要性": required_str,
                    "類別": rule_class_map.get(keyword, "未知")
                })
            # 依類別 groupby，計算 rowspan
            from collections import OrderedDict
            grouped = OrderedDict()
            for row in table_data:
                grouped.setdefault(row["類別"], []).append(row)
            # 類別底色
            class_colors = ["#e6f2ff", "#f9f9d1", "#e8f6e8", "#ffe6e6", "#f3e6ff", "#fff2cc"]
            class_color_map = {}
            for idx, k in enumerate(grouped.keys()):
                class_color_map[k] = class_colors[idx % len(class_colors)]
            # 產生 HTML 表格，規則名稱 hover 顯示規則說明
            html = '''<style>
            .score-table th, .score-table td { border:1px solid #bbb; padding:8px 12px; text-align:center; font-size:16px; }
            .score-table th { background:#2c5c88; color:#fff; }
            .score-table .class-cell { cursor: pointer; position:relative; }
            .class-tooltip { display:none; position:absolute; left:100%; top:50%; transform:translateY(-50%); background:#fff; color:#222; border:1.5px solid #2c5c88; border-radius:10px; padding:16px 28px; min-width:260px; max-width:480px; box-shadow:0 4px 16px #888; z-index:99999; font-size:16px; text-align:left; white-space:pre-line; word-break:break-all; }
            .class-cell:hover .class-tooltip { display:block; }
            .score-table .rule-link { color: #222; text-decoration: none; cursor: default; position:relative; }
            .score-table td { background:#fff; }
            .rule-tooltip { display:none; position:absolute; left:100%; top:50%; transform:translateY(-50%); background:#fff; color:#222; border:1.5px solid #1a5fb4; border-radius:8px; padding:10px 16px; min-width:180px; max-width:320px; box-shadow:0 2px 8px #888; z-index:9999; font-size:15px; white-space:pre-line; }
            .rule-link:hover .rule-tooltip { display:block; }
            </style>
            <div><table class="score-table" style="border-collapse:collapse;width:100%;min-width:600px;">
            <tr><th>分數</th><th>規則名稱</th><th>必要性</th><th>類別</th></tr>
            '''
            for idx, (cls, rows) in enumerate(grouped.items()):
                rowspan = len(rows)
                color = class_color_map[cls]
                for i, row in enumerate(rows):
                    html += "<tr>"
                    html += f"<td>{row['分數']}</td>"
                    rule_key = row['規則名稱']
                    rule_desc = rule_explain_map.get(rule_key, '')
                    # 條列式美化規則說明
                    def beautify_rule_desc(desc):
                        import re
                        # 將 "；" 或 ";" 或 "\n" 分割
                        items = re.split(r'[；;\n]+', desc)
                        items = [i.strip() for i in items if i.strip()]
                        # 將 "：" 或 ":" 分割分數
                        html_list = []
                        for item in items:
                            if '：' in item:
                                k, v = item.split('：', 1)
                                v = v.strip()
                                if not v.endswith('分'):
                                    v = v + '分'
                                html_list.append(f'<li>📊 <b>{k}</b>：<span style="color:#1a5fb4;font-weight:bold">{v}</span></li>')
                            elif ':' in item:
                                k, v = item.split(':', 1)
                                v = v.strip()
                                if not v.endswith('分'):
                                    v = v + '分'
                                html_list.append(f'<li>📊 <b>{k}</b>：<span style="color:#1a5fb4;font-weight:bold">{v}</span></li>')
                            else:
                                html_list.append(f'<li>{item}</li>')
                        return '<ul style="margin:0 0 0 1em;padding:0;list-style:none;text-align:left;">' + ''.join(html_list) + '</ul>' if html_list else desc
                    beautified = beautify_rule_desc(rule_desc)
                    # 規則名稱加上 hover 條列美化說明
                    html += f"<td><span class='rule-link'>{row['規則名稱顯示']}<span class='rule-tooltip'>{beautified}</span></span></td>"
                    html += f"<td>{row['必要性']}</td>"
                    if i == 0:
                        desc = class_desc_map.get(cls, "")
                        # 美化類別 hover 浮窗
                        html += f"<td rowspan='{rowspan}' class='class-cell' style='background:{color};font-weight:bold;min-width:90px;position:relative;'>{cls}"
                        if desc:
                            html += f"<span class='class-tooltip'><b>📂 {cls}</b><br>{desc}</span>"
                        html += "</td>"
                    html += "</tr>"
            html += "</table></div>"
        else:
            st.info("尚未有 AI 分析結果")