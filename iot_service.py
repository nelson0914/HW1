"""
iot_service.py - 整合台灣即時氣象測站與 Edimax AirBox 開放資料服務模組
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import database

# 快取機制：避免重複請求遠端伺服器 (TTL 設為 300 秒 / 5 分鐘)
_CACHE = {
    "taiwan_weather": {"data": None, "timestamp": 0},
    "airbox": {"data": None, "timestamp": 0}
}
CACHE_TTL = 300

# 請求標頭 (表明學術教學與應用物聯網研究身份，避免被誤認為惡意爬蟲)
REQUEST_HEADERS = {
    "User-Agent": "Taiwan-IoT-Academic-Course-Project/1.0 (Master Degree IoT Coursework; Contact: student-project@university.edu.tw)",
    "Accept": "application/json, text/plain, */*",
}

# 縣市至六大分區映射表 (HW10 規範)
COUNTY_TO_REGION = {
    "基隆市": "北部地區", "臺北市": "北部地區", "新北市": "北部地區", "桃園市": "北部地區",
    "新竹市": "北部地區", "新竹縣": "北部地區", "苗栗縣": "北部地區",
    "臺中市": "中部地區", "彰化縣": "中部地區", "南投縣": "中部地區", "雲林縣": "中部地區",
    "嘉義市": "中部地區", "嘉義縣": "中部地區",
    "臺南市": "南部地區", "高雄市": "南部地區", "屏東縣": "南部地區",
    "宜蘭縣": "東北部地區",
    "花蓮縣": "東部地區",
    "臺東縣": "東南部地區",
    "澎湖縣": "南部地區", "金門縣": "中部地區", "連江縣": "北部地區"
}


def fetch_taiwan_weather_map_data(force_refresh: bool = False) -> Tuple[bool, str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    從 https://taiwan-weather-map.vercel.app/api/weather/current 取得最新 CWA 氣象站觀測資料
    合規性：該端點為公開開放的 CWA O-A0003-001 彙整資料。
    回傳：
      - success (bool)
      - message (str)
      - region_forecasts (List[Dict]): 符合微課程 TemperatureForecasts 規格的分區日預報/現況
      - station_points (List[Dict]): 供 Folium 地圖標示的 360+ 個實體氣象站觀測點
    """
    now = time.time()
    if not force_refresh and _CACHE["taiwan_weather"]["data"] and (now - _CACHE["taiwan_weather"]["timestamp"] < CACHE_TTL):
        cached = _CACHE["taiwan_weather"]["data"]
        return True, "從本地合規快取載入台灣氣象地圖資料 (快取效期 5 分鐘)", cached["regions"], cached["stations"]

    url = "https://taiwan-weather-map.vercel.app/api/weather/current"
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=12)
        if resp.status_code != 200:
            return False, f"連線至台灣氣象地圖失敗，HTTP 狀態碼: {resp.status_code}", [], []

        raw_json = resp.json()
        features = raw_json.get("data", {}).get("features", [])
        if not features:
            return False, "成功連線但回傳資料中未包含觀測站 features。", [], []

        today_str = datetime.now().strftime("%Y-%m-%d")
        region_temps: Dict[str, List[float]] = {}
        station_points = []

        for f in features:
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [0, 0])

            temp = props.get("temperature")
            county = props.get("county", "")
            town = props.get("town", "")
            station_id = props.get("stationId", "")
            weather = props.get("weather", "多雲")
            humidity = props.get("humidity", 70)

            # 排除異常或缺測值 (-99, None 等)
            if temp is None or temp < -10 or temp > 50:
                continue

            region_name = COUNTY_TO_REGION.get(county, "中部地區")
            if region_name not in region_temps:
                region_temps[region_name] = []
            region_temps[region_name].append(temp)

            station_points.append({
                "stationId": station_id,
                "county": county,
                "town": town,
                "lon": coords[0],
                "lat": coords[1],
                "temperature": float(temp),
                "humidity": humidity,
                "weather": weather,
                "regionName": region_name
            })

        # 將 360+ 測站數據聚合為 5 大分區的 MinT / MaxT
        region_forecasts = []
        for r_name, t_list in region_temps.items():
            if t_list:
                min_t = round(min(t_list), 1)
                max_t = round(max(t_list), 1)
                region_forecasts.append({
                    "regionName": r_name,
                    "dataDate": today_str,
                    "minT": min_t,
                    "maxT": max_t
                })

        # 寫入快取
        _CACHE["taiwan_weather"]["data"] = {"regions": region_forecasts, "stations": station_points}
        _CACHE["taiwan_weather"]["timestamp"] = now

        return True, f"成功同步台灣氣象地圖資料 (涵蓋 {len(station_points)} 座氣象觀測站、{len(region_forecasts)} 大分區)", region_forecasts, station_points

    except requests.exceptions.Timeout:
        return False, "連線至台灣氣象地圖逾時，請檢查網路連線。", [], []
    except Exception as e:
        return False, f"讀取台灣氣象地圖發生錯誤: {str(e)}", [], []


def fetch_airbox_edimax_data(force_refresh: bool = False, max_records: int = 150) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    從 Edimax AirBox / 中研院資訊所 LASS Open Data 取得台灣空氣盒子即時感測數據
    合規性：訊舟科技 (Edimax) 官方合作之中研院 IIS-NRL 開放感測社群端點 (合法公開開放資料)。
    回傳：
      - success (bool)
      - message (str)
      - airbox_records (List[Dict]): 包含站名、經緯度、溫度、濕度、PM2.5、時間
    """
    now = time.time()
    if not force_refresh and _CACHE["airbox"]["data"] and (now - _CACHE["airbox"]["timestamp"] < CACHE_TTL):
        return True, "從本地合規快取載入 AirBox 物聯網資料 (快取效期 5 分鐘)", _CACHE["airbox"]["data"]

    # 官方合作開放資料鏡像端點 (中研院資訊所 IIS-NRL AirBox Open Data)
    url = "https://pm25.lass-net.org/data/last-all-airbox.json"
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
        if resp.status_code != 200:
            return False, f"無法連線至 AirBox 開放資料平台，狀態碼: {resp.status_code}", []

        data = resp.json()
        feeds = data.get("feeds", [])
        if not feeds:
            return False, "AirBox 開放資料中未包含感測節點 (feeds 為空)。", []

        records = []
        for item in feeds:
            # 僅篩選具有完整經緯度與溫度數值的節點
            site_name = item.get("SiteName", item.get("device_id", "未知感測站"))
            lat = item.get("gps_lat")
            lon = item.get("gps_lon")
            temp = item.get("s_t0")  # 溫度
            hum = item.get("s_h0")   # 濕度
            pm25 = item.get("s_d0")  # PM2.5
            area = item.get("area", "台灣")
            time_str = f"{item.get('date', '')} {item.get('time', '')}".strip()

            # 基本數值過濾 (台灣合理經緯度：21.5~26.5 N, 119~122.5 E)
            if lat is None or lon is None or temp is None:
                continue
            if not (21.0 <= lat <= 26.5 and 118.0 <= lon <= 123.0):
                continue

            records.append({
                "siteName": str(site_name),
                "area": str(area),
                "lat": float(lat),
                "lon": float(lon),
                "temperature": round(float(temp), 1),
                "humidity": round(float(hum), 1) if hum is not None else 70.0,
                "pm25": round(float(pm25), 1) if pm25 is not None else 15.0,
                "observedTime": time_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            if len(records) >= max_records:
                break

        _CACHE["airbox"]["data"] = records
        _CACHE["airbox"]["timestamp"] = now

        return True, f"成功同步 Edimax AirBox 物聯網開放資料 (共載入 {len(records)} 個實體 IoT 感測節點)", records

    except requests.exceptions.Timeout:
        return False, "連線至 AirBox 開放資料逾時，請檢查網路連線。", []
    except Exception as e:
        return False, f"讀取 AirBox 物聯網資料發生錯誤: {str(e)}", []
