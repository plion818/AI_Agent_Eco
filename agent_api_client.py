# 智慧核保Agent API 回傳內容自動解析 Canvas
import os
import json
import logging
import requests
import re
from dotenv import load_dotenv

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 讀取 .env 檔案
load_dotenv()

def call_agent_api(customer_data: dict, rules: dict, timeout: int = 60):
    """
    自動化呼叫 AGENT API，傳送客戶資訊與規則，回傳 API 結果或 None。
    timeout: 逾時秒數，預設 60 秒
    """
    api_url = os.getenv("API_URL")
    api_token = os.getenv("API_TOKEN")  # 若你的API不需token，這行可刪
    if not api_url:
        logger.error("缺少 API_URL，請確認 .env 檔案設定。")
        return None

    # 封裝 input_value 與 payload
    input_content = {
        "customer_info": customer_data,
        "rules": rules
    }
    payload = {
        "input_value": json.dumps(input_content, ensure_ascii=False),
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {}
    }
    headers = {'Content-Type': 'application/json'}
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
        logger.info(f"API 回應狀態碼: {response.status_code}")
        logger.debug(f"API 回應內容: {response.text}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"API 呼叫失敗：{e}")
        return None

# Canvas 區塊：自動解析最終回傳小工具

def extract_final_results(api_response):
    """
    從Langflow智慧核保API回傳物件中自動萃取'擷取結果'與'分析'內容
    Args:
        api_response (dict): API呼叫回傳的原始JSON物件
    Returns:
        dict: {"extracted": {...}, "analysis": {...}} 或 None
    """
    try:
        # 多層message
        text = (
            api_response["outputs"][0]
            ["outputs"][0]
            ["results"]["message"]["text"]
        )
        # 去掉 markdown 或 codeblock
        text = text.strip()
        match = re.search(r"```json\s*({.*})\s*```", text, re.DOTALL)
        json_text = match.group(1) if match else text
        result = json.loads(json_text)
        return result
    except Exception as e:
        logger.error(f"解析API回應內容失敗：{e}")
        logger.error(f"解析失敗內容原文: {text}")
        return None

if __name__ == "__main__":
    import sys

    # 讀入規則
    import config_rules
    rules = None
    for var in dir(config_rules):
        if not var.startswith("__"):
            value = getattr(config_rules, var)
            if isinstance(value, dict):
                rules = value
                break
    if rules is None:
        raise ValueError('config_rules.py 未找到任何 dict 規則變數')

    # 取得 customer_id（命令列參數優先，否則互動輸入）
    if len(sys.argv) > 1:
        customer_id = sys.argv[1]
    else:
        customer_id = input("請輸入要查詢的 customer_id（如 C00009）：").strip()

    # 取得 timeout（可選，命令列第2參數，否則預設60秒）
    if len(sys.argv) > 2:
        try:
            timeout = int(sys.argv[2])
        except ValueError:
            print("timeout 參數需為整數，將使用預設60秒")
            timeout = 60
    else:
        timeout = 60

    # 讀取客戶基本資料
    try:
        with open("客戶基本資訊/基本資訊.json", "r", encoding="utf-8") as f:
            basic_info = json.load(f)
    except Exception as e:
        logger.error(f"讀取基本資訊失敗：{e}")
        exit(1)

    # 讀取客戶過往紀錄
    try:
        with open("客戶過往紀錄/過往紀錄.json", "r", encoding="utf-8") as f:
            history_info = json.load(f)
    except Exception as e:
        logger.error(f"讀取過往紀錄失敗：{e}")
        exit(1)

    # 依指定 customer_id 查詢
    customer_base = next((c for c in basic_info if c.get("customer_id") == customer_id), None)
    customer_hist = next((h for h in history_info if h.get("customer_id") == customer_id), None)

    if not customer_base:
        logger.error(f"找不到 {customer_id} 的基本資料")
        exit(1)

    # 合併欄位（flat結構）
    customer_data = customer_base.copy()
    if customer_hist:
        for k, v in customer_hist.items():
            if k != "customer_id":
                customer_data[k] = v

    # 呼叫 API 並顯示
    result = call_agent_api(customer_data, rules, timeout=timeout)
    print("="*30)
    print("本次傳送 payload：")
    input_content = {
        "customer_info": customer_data,
        "rules": rules
    }
    payload = {
        "input_value": json.dumps(input_content, ensure_ascii=False),
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {}
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    print("="*30)
    if result:
        # Canvas小工具自動解析
        final_result = extract_final_results(result)
        print("="*30)
        if final_result:
            print("【自動解析最終擷取結果與分析】")
            print(json.dumps(final_result, ensure_ascii=False, indent=2))
        else:
            print("❌ 解析 API 回傳內容失敗，請檢查結構或日誌")
    else:
        logger.warning("API 未取得回應或發生錯誤。")
