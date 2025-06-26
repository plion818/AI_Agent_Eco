import streamlit as st
import json
import os

# 讀取基本資料
with open("客戶基本資訊/基本資訊.json", "r", encoding="utf-8") as f:
    customers = json.load(f)

# 讀取過往紀錄
with open("客戶過往紀錄/過往紀錄.json", "r", encoding="utf-8") as f:
    records = json.load(f)

# 建立 customer_id -> 基本資料對照表
customer_dict = {c["name"]: c for c in customers}
id_to_record = {r["customer_id"]: r for r in records}

st.title("客戶資料查詢")

# 客戶姓名下拉選單
names = [c["name"] for c in customers]
selected_name = st.selectbox("請選擇客戶姓名", names)

if selected_name:
    customer = customer_dict[selected_name]
    st.subheader("基本資料")
    st.json(customer)

    if st.button("查詢過往紀錄"):
        record = id_to_record.get(customer["customer_id"])
        if record:
            st.subheader("過往紀錄")
            # 信用評等
            st.write(f"信用評等：{record['credit_rating']}")
            # 信用警示
            st.write("信用警示：")
            st.json(record["credit_alert"])
            # 保單歷史
            st.write("保單歷史：")
            st.table(record["insurance_history"])
            # 理賠紀錄
            st.write("理賠紀錄：")
            st.table(record["claim_records"])
            # 審查紀錄
            st.write("審查紀錄：")
            st.json(record["review_records"])
            # 可疑交易
            st.write("可疑交易：")
            st.json(record["suspicious_transaction"])
            # 刑事紀錄
            st.write("刑事紀錄：")
            st.json(record["criminal_record"])
            # 現有資產
            st.write("現有資產：" + "，".join(record["current_assets"]))
        else:
            st.warning("查無過往紀錄。")