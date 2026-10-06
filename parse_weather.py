"""
parse_weather.py - 分析 JSON，提取氣溫資料
模組 2：分析 JSON，提取氣溫資料 (20%)

目標：
  分析 JSON 結構，找出並提取每日最高與最低氣溫。
  (Region 在資料中通常以 Location 表示)

分析重點 (JSON 巢狀階層)：
  JSON
  └── records
      └── locations
          └── location[] (地區)
              └── weatherElement[] (天氣要素)
                  └── time[] (預報日期)
                      ├── elementName: MinT (最低溫)
                      └── elementName: MaxT (最高溫)

提取結果範例：
  regionName | dataDate   | mint | maxt
  北部地區   | 2026-04-14 | 18   | 26
  中部地區   | 2026-04-14 | 20   | 30
  南部地區   | 2026-04-14 | 22   | 31

輸出：
  產出 weather_data.csv 供存入 SQLite 資料庫使用

評分項目：
  提取正確 10% | 觀察資料 5% | 程式品質 5%
"""

import json
import os
import sys
import pandas as pd
from typing import List, Dict, Any

# 確保 Windows 命令提示字元編碼相容性 (防止 cp950 編碼問題)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

INPUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cwa_weather_raw.json")
OUTPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data.csv")

def parse_weather_json(json_path: str = INPUT_JSON) -> List[Dict[str, Any]]:
    """
    從 JSON 中提取六大分區每日之 MinT 與 MaxT
    """
    if not os.path.exists(json_path):
        print(f"⚠️ 找不到 {json_path}，嘗試先呼叫 fetch_weather.py...")
        import fetch_weather
        fetch_weather.main()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records_obj = data.get("records", {})
    locations_list = []

    # 解析 locations -> location[] 階層
    if "locations" in records_obj:
        for loc_group in records_obj["locations"]:
            locations_list.extend(loc_group.get("location", []))
    elif "location" in records_obj:
        locations_list = records_obj["location"]

    extracted = []

    for loc in locations_list:
        region_name = loc.get("locationName", "")
        weather_elements = loc.get("weatherElement", [])

        min_times = []
        max_times = []

        for elem in weather_elements:
            elem_name = elem.get("elementName", "")
            if elem_name in ["MinT", "MinTemperature"]:
                min_times = elem.get("time", [])
            elif elem_name in ["MaxT", "MaxTemperature"]:
                max_times = elem.get("time", [])

        # 依序匹配時間點提取氣溫
        for min_e, max_e in zip(min_times, max_times):
            start_str = min_e.get("startTime", "") or min_e.get("dataTime", "")
            date_str = start_str.split(" ")[0].split("T")[0]

            def extract_val(elem_entry):
                if "elementValue" in elem_entry and elem_entry["elementValue"]:
                    return float(elem_entry["elementValue"][0].get("value", 0))
                if "parameter" in elem_entry:
                    return float(elem_entry["parameter"].get("parameterName", 0))
                return 0.0

            mint = extract_val(min_e)
            maxt = extract_val(max_e)

            extracted.append({
                "regionName": region_name,
                "dataDate": date_str,
                "mint": mint,
                "maxt": maxt
            })

    return extracted


def main():
    print("=" * 60)
    print("🔬 步驟 2：分析 JSON 結構並提取每日最低 (MinT) 與最高 (MaxT) 氣溫")
    print("=" * 60)

    records = parse_weather_json(INPUT_JSON)
    if not records:
        print("❌ 未成功提取到氣溫紀錄，請確認 JSON 資料結構。")
        return

    df = pd.DataFrame(records)

    # 產出 weather_data.csv 中間產物
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"✅ 成功提取 {len(df)} 筆氣溫紀錄！")
    print(f"💾 中間產物已儲存至：{OUTPUT_CSV}\n")

    print("📊 提取結果範例 (首日前三區域)：")
    print("-" * 50)
    sample_preview = df[df["dataDate"] == df["dataDate"].min()][["regionName", "dataDate", "mint", "maxt"]].head(3)
    print(sample_preview.to_string(index=False))
    print("-" * 50)

    print("\n👉 請繼續執行第三步：python database.py\n")


if __name__ == "__main__":
    main()
