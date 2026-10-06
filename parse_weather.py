"""
parse_weather.py - 分析 JSON，提取氣溫資料
模組 2：分析 JSON，提取氣溫資料 (20%)

目標：
  分析 JSON 結構，找出並提取每日最高與最低氣溫。
  涵蓋六大分區：北部地區、中部地區、南部地區、東北部地區、東部地區、東南部地區

分析重點 (JSON 巢狀階層)：
  JSON (F-D0047-091)
  └── records
      └── Locations[]
          └── Location[] (各縣市)
              └── WeatherElement[] (天氣要素)
                  ├── ElementName: 最低溫度 (MinT)
                  └── ElementName: 最高溫度 (MaxT)

提取結果：
  regionName | dataDate   | mint | maxt
  六大分區未來 7 天氣溫預報

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
import cwa_service

# 確保 Windows 命令提示字元編碼相容性
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

INPUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cwa_weather_raw.json")
OUTPUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data.csv")

def parse_weather_json(json_path: str = INPUT_JSON) -> List[Dict[str, Any]]:
    """
    從 JSON 中提取六大分區每日之 MinT 與 MaxT (共 7 天)
    """
    if not os.path.exists(json_path):
        print(f"⚠️ 找不到 {json_path}，嘗試先呼叫 fetch_weather.py...")
        import fetch_weather
        fetch_weather.main()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 透過 cwa_service 的強健解析器進行結構提取
    extracted = cwa_service.parse_cwa_json(data)
    return extracted


def main():
    print("=" * 60)
    print("🔬 步驟 2：分析 JSON 結構並提取六大分區 7 天每日最低 (MinT) 與最高 (MaxT) 氣溫")
    print("=" * 60)

    records = parse_weather_json(INPUT_JSON)
    if not records:
        print("❌ 未成功提取到氣溫紀錄，請確認 JSON 資料結構。")
        return

    df = pd.DataFrame(records)

    # 產出 weather_data.csv 中間產物
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print(f"✅ 成功提取 {len(df)} 筆氣溫紀錄 (涵蓋 6 大分區完整 7 天預報)！")
    print(f"💾 中間產物已儲存至：{OUTPUT_CSV}\n")

    print("📊 提取結果預覽 (前 6 筆，即今日六大分區氣溫)：")
    print("-" * 50)
    print(df.head(6)[["regionName", "dataDate", "minT", "maxT"]].to_string(index=False))
    print("-" * 50)

    print("\n👉 請繼續執行第三步：python database.py\n")


if __name__ == "__main__":
    main()
