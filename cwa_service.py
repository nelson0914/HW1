"""
cwa_service.py - 中央氣象署 (CWA) API 擷取、JSON 解析與資料同步服務
對應微課程步驟：
  - 步驟 3: 中央氣象署 CWA Open Data 平台
  - 步驟 4: API 資料取得 (使用 Requests 取得 JSON)
  - 步驟 5: JSON 資料結構解析 (解析 locations / weatherElement)
  - 步驟 6: 提取最高與最低氣溫 (MinT / MaxT)
  - 步驟 7: 資料整理與預覽 (Pandas 結構化處理)
  - 步驟 20: 程式碼品質與防呆設計 (支援使用者自訂 API 網址、API Key、錯誤處理)
"""

import requests
import json
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import database

# 預設中央氣象署開放資料 API 端點 (全台未來一週天氣預報 / 一般天氣預報)
DEFAULT_CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"

# 台灣主要分區地理座標與預設縣市參照
REGION_METADATA = {
    "北部地區": {"lat": 25.0375, "lon": 121.5637, "desc": "包含基隆、臺北、新北、桃園、新竹"},
    "中部地區": {"lat": 24.1477, "lon": 120.6736, "desc": "包含苗栗、臺中、彰化、南投、雲林"},
    "南部地區": {"lat": 22.6273, "lon": 120.3014, "desc": "包含嘉義、臺南、高雄、屏東"},
    "東北部地區": {"lat": 24.7570, "lon": 121.7530, "desc": "包含宜蘭縣與東北角地區"},
    "東南部地區": {"lat": 23.9872, "lon": 121.6016, "desc": "包含花蓮、臺東地區"},
}

def generate_sample_forecast_data(start_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    生成標準範例預報資料 (模擬微課程投影片中的數據情境)
    涵蓋北部、中部、南部、東北部、東南部等主要地區的一週氣溫預報。
    """
    if not start_date_str:
        # 使用投影片中的 2026-04-14 或當前日期
        base_date = datetime.now().date()
    else:
        try:
            base_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            base_date = datetime.now().date()

    # 基準溫度模型 (不同地區的溫度特性)
    region_base_temps = {
        "北部地區": {"min": 19.0, "max": 27.5},
        "中部地區": {"min": 21.0, "max": 31.0},
        "南部地區": {"min": 23.0, "max": 32.5},
        "東北部地區": {"min": 18.5, "max": 26.0},
        "東南部地區": {"min": 22.0, "max": 29.5},
    }

    records = []
    # 產生未來 7 天資料
    for day_offset in range(7):
        target_date = base_date + timedelta(days=day_offset)
        target_date_str = target_date.strftime("%Y-%m-%d")

        # 每天微幅波動模擬自然氣溫變化
        wave = (day_offset % 3 - 1) * 0.8

        for region, base in region_base_temps.items():
            min_t = round(base["min"] + wave + (0.3 if region == "中部地區" else 0.0), 1)
            max_t = round(base["max"] + wave * 1.2 + (0.5 if region == "南部地區" else 0.0), 1)
            records.append({
                "regionName": region,
                "dataDate": target_date_str,
                "minT": min_t,
                "maxT": max_t,
            })

    return records


def parse_cwa_json(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    步驟 5 & 6：解析中央氣象署 JSON 資料格式
    支援 CWA F-C0032-001 (一般天氣預報) 與 F-D0047-091 (一週天氣預報)，
    同時兼容通用陣列格式。
    """
    parsed_records = []

    # 情況 1：直接是標準的字典陣列 (若使用者提供的自訂 API 直接回傳結構化 JSON)
    if isinstance(json_data, list):
        for item in json_data:
            if isinstance(item, dict) and "regionName" in item and "dataDate" in item:
                parsed_records.append({
                    "regionName": str(item.get("regionName")),
                    "dataDate": str(item.get("dataDate")),
                    "minT": float(item.get("minT", 20.0)),
                    "maxT": float(item.get("maxT", 28.0))
                })
        if parsed_records:
            return parsed_records

    # 情況 2：中央氣象署 CWA 標準階層 records -> locations / location
    records_obj = json_data.get("records", {})

    # 處理 F-D0047-091 結構 (locations -> location)
    locations_list = []
    if "locations" in records_obj:
        for loc_group in records_obj["locations"]:
            locations_list.extend(loc_group.get("location", []))
    elif "location" in records_obj:
        locations_list = records_obj["location"]

    if locations_list:
        # 地區對應關係 (將縣市歸納至五大地區，或直接使用縣市名)
        county_to_region = {
            "臺北市": "北部地區", "新北市": "北部地區", "基隆市": "北部地區", "桃園市": "北部地區", "新竹市": "北部地區", "新竹縣": "北部地區",
            "苗栗縣": "中部地區", "臺中市": "中部地區", "彰化縣": "中部地區", "南投縣": "中部地區", "雲林縣": "中部地區",
            "嘉義市": "南部地區", "嘉義縣": "南部地區", "臺南市": "南部地區", "高雄市": "南部地區", "屏東縣": "南部地區",
            "宜蘭縣": "東北部地區",
            "花蓮縣": "東南部地區", "臺東縣": "東南部地區",
            "澎湖縣": "南部地區", "金門縣": "中部地區", "連江縣": "北部地區"
        }

        # 暫存每日每區的氣溫清單以計算平均或代表值
        region_date_data: Dict[Tuple[str, str], Dict[str, List[float]]] = {}

        for loc in locations_list:
            raw_name = loc.get("locationName", "")
            # 若原始資料就是「中部地區」等直接使用，否則映射縣市
            region_name = raw_name if "地區" in raw_name else county_to_region.get(raw_name, raw_name)

            weather_elements = loc.get("weatherElement", [])
            min_t_elements = []
            max_t_elements = []

            for elem in weather_elements:
                elem_name = elem.get("elementName", "")
                if elem_name in ["MinT", "MinTemperature"]:
                    min_t_elements = elem.get("time", [])
                elif elem_name in ["MaxT", "MaxTemperature"]:
                    max_t_elements = elem.get("time", [])

            # 配對時間與溫度
            for min_entry, max_entry in zip(min_t_elements, max_t_elements):
                start_time = min_entry.get("startTime", "") or min_entry.get("dataTime", "")
                if not start_time:
                    continue
                date_str = start_time.split(" ")[0].split("T")[0]

                # 提取數值
                try:
                    min_val = float(min_entry.get("parameter", {}).get("parameterName", min_entry.get("elementValue", [{}])[0].get("value", 20.0)))
                    max_val = float(max_entry.get("parameter", {}).get("parameterName", max_entry.get("elementValue", [{}])[0].get("value", 28.0)))
                except (ValueError, TypeError, IndexError):
                    min_val, max_val = 20.0, 28.0

                key = (region_name, date_str)
                if key not in region_date_data:
                    region_date_data[key] = {"minT": [], "maxT": []}
                region_date_data[key]["minT"].append(min_val)
                region_date_data[key]["maxT"].append(max_val)

        # 整合計算
        for (r_name, d_str), vals in region_date_data.items():
            avg_min = round(sum(vals["minT"]) / len(vals["minT"]), 1)
            avg_max = round(sum(vals["maxT"]) / len(vals["maxT"]), 1)
            parsed_records.append({
                "regionName": r_name,
                "dataDate": d_str,
                "minT": avg_min,
                "maxT": avg_max
            })

    return parsed_records


def fetch_weather_from_url(
    url: str,
    api_key: Optional[str] = None,
    timeout: int = 10
) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    步驟 4：使用 Requests 取得 API 資料
    支援 Authorization Header 或是 URL 查詢參數注入
    支援使用者後續提供的任何 Data URL。
    """
    headers = {}
    params = {}

    if api_key:
        api_key = api_key.strip()
        headers["Authorization"] = api_key
        params["Authorization"] = api_key

    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        if response.status_code != 200:
            return False, f"HTTP 連線失敗，狀態碼: {response.status_code} ({response.reason})", []

        try:
            data = response.json()
        except Exception as e:
            return False, f"JSON 解析失敗: 回傳內容非標準 JSON 格式 ({str(e)})", []

        records = parse_cwa_json(data)
        if not records:
            return False, "成功取得 JSON，但無法找到符合規格的氣象預報資料結構 (請確認欄位是否包含 location 或 MinT/MaxT)。", []

        return True, f"成功取得並解析 {len(records)} 筆氣溫預報記錄！", records

    except requests.exceptions.Timeout:
        return False, f"連線逾時 ({timeout} 秒)，請檢查網路或該網站連線狀態。", []
    except requests.exceptions.RequestException as e:
        return False, f"網路請求發生異常: {str(e)}", []


def sync_data_to_sqlite(records: List[Dict[str, Any]]) -> Tuple[int, str]:
    """
    步驟 8 & 20：儲存或更新至 SQLite 資料庫 (data.db)
    """
    try:
        database.init_db()
        count = database.insert_forecasts(records)
        return count, f"已成功將 {count} 筆資料寫入/更新至 data.db 的 TemperatureForecasts 資料表！"
    except Exception as e:
        return 0, f"寫入 SQLite 資料庫失敗: {str(e)}"
