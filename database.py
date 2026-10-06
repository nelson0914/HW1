"""
database.py - SQLite 資料庫操作模組
對應微課程步驟：
  - 步驟 8: 建立 SQLite 資料庫 (data.db)
  - 步驟 9: 資料庫設計 (TemperatureForecasts 資料表)
  - 步驟 10: 查詢資料驗證 (SQL 查詢語法)
  - 步驟 12: 從資料庫讀取資料 (Pandas 整合)
  - 步驟 20: 程式碼品質與防呆設計 (重複執行不重複插入、UPSERT 機制)
  - 擴充: AirBox 台灣物聯網感測節點資料表 (支援應用物聯網作業)
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
import os
import sys

# 確保 Windows 命令提示字元編碼相容性 (防止 cp950 編碼問題)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.db")


def get_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    """取得 SQLite 資料庫連線，設定 Row 廠牌以便進行欄位字典訪問"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_FILE) -> None:
    """
    步驟 8 & 9：建立資料庫與必要資料表
      1. TemperatureForecasts (微課程標準資料表)
      2. AirBoxReadings (物聯網感測器即時資料表)
    """
    create_forecasts_table = """
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT NOT NULL,
        dataDate TEXT NOT NULL,
        minT REAL NOT NULL,
        maxT REAL NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(regionName, dataDate)
    );
    """

    create_airbox_table = """
    CREATE TABLE IF NOT EXISTS AirBoxReadings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        siteName TEXT NOT NULL,
        area TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        temperature REAL,
        humidity REAL,
        pm25 REAL,
        observedTime TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(siteName, observedTime)
    );
    """

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_forecasts_table)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_region_date ON TemperatureForecasts(regionName, dataDate);")
        cursor.execute(create_airbox_table)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_airbox_site ON AirBoxReadings(siteName, observedTime);")
        conn.commit()


def insert_forecasts(records: List[Dict[str, Any]], db_path: str = DB_FILE) -> int:
    """
    模組 3 & 重複執行不重複插入 (UPSERT)
    使用 SQLite 的 ON CONFLICT(regionName, dataDate) DO UPDATE
    確保重複執行更新時直接更新 mint 與 maxt，不產生重複記錄。
    """
    if not records:
        return 0

    # 統一鍵名相容 mint/minT 與 maxt/maxT
    normalized = []
    for r in records:
        mint_val = r.get("mint", r.get("minT", 20.0))
        maxt_val = r.get("maxt", r.get("maxT", 28.0))
        normalized.append({
            "regionName": str(r.get("regionName")),
            "dataDate": str(r.get("dataDate")),
            "mint": float(mint_val),
            "maxt": float(maxt_val)
        })

    upsert_sql = """
    INSERT INTO TemperatureForecasts (regionName, dataDate, minT, maxT, updated_at)
    VALUES (:regionName, :dataDate, :mint, :maxt, CURRENT_TIMESTAMP)
    ON CONFLICT(regionName, dataDate) DO UPDATE SET
        minT = excluded.minT,
        maxT = excluded.maxT,
        updated_at = CURRENT_TIMESTAMP;
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(upsert_sql, normalized)
        conn.commit()
        return cursor.rowcount


def insert_airbox_readings(records: List[Dict[str, Any]], db_path: str = DB_FILE) -> int:
    """寫入/更新 Edimax AirBox 物聯網感測數值 (UPSERT)"""
    if not records:
        return 0

    upsert_sql = """
    INSERT INTO AirBoxReadings (siteName, area, lat, lon, temperature, humidity, pm25, observedTime, updated_at)
    VALUES (:siteName, :area, :lat, :lon, :temperature, :humidity, :pm25, :observedTime, CURRENT_TIMESTAMP)
    ON CONFLICT(siteName, observedTime) DO UPDATE SET
        temperature = excluded.temperature,
        humidity = excluded.humidity,
        pm25 = excluded.pm25,
        updated_at = CURRENT_TIMESTAMP;
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(upsert_sql, records)
        conn.commit()
        return cursor.rowcount


def get_distinct_regions(db_path: str = DB_FILE) -> List[str]:
    """步驟 10：SELECT DISTINCT regionName FROM TemperatureForecasts;"""
    sql = "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName ASC;"
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [row[0] for row in rows]


def get_distinct_dates(db_path: str = DB_FILE) -> List[str]:
    """查詢資料庫中所有不重複的日期"""
    sql = "SELECT DISTINCT dataDate FROM TemperatureForecasts ORDER BY dataDate ASC;"
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [row[0] for row in rows]


def get_forecasts_by_region(region_name: str, db_path: str = DB_FILE) -> pd.DataFrame:
    """
    步驟 10 & 12：依地區查詢氣溫預報資料
    SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區' ORDER BY dataDate;
    """
    sql = """
    SELECT regionName, dataDate, minT, maxT, ROUND((minT + maxT) / 2.0, 1) AS avgT
    FROM TemperatureForecasts
    WHERE regionName = ?
    ORDER BY dataDate ASC;
    """
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=[region_name])


def get_forecasts_by_date(date_str: str, db_path: str = DB_FILE) -> pd.DataFrame:
    """查詢特定日期的全台各區氣溫預報，供地圖繪製與指標統計使用"""
    sql = """
    SELECT regionName, dataDate, minT, maxT, ROUND((minT + maxT) / 2.0, 1) AS avgT
    FROM TemperatureForecasts
    WHERE dataDate = ?
    ORDER BY regionName ASC;
    """
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=[date_str])


def get_all_forecasts(db_path: str = DB_FILE) -> pd.DataFrame:
    """步驟 12：讀取全部預報資料 (SELECT * FROM TemperatureForecasts)"""
    sql = """
    SELECT id, regionName, dataDate, minT, maxT,
           ROUND((minT + maxT) / 2.0, 1) AS avgT,
           updated_at
    FROM TemperatureForecasts
    ORDER BY dataDate ASC, regionName ASC;
    """
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn)


def get_all_airbox_readings(db_path: str = DB_FILE, limit: int = 300) -> pd.DataFrame:
    """讀取 AirBox 物聯網最新觀測數據"""
    sql = f"""
    SELECT siteName, area, lat, lon, temperature, humidity, pm25, observedTime, updated_at
    FROM AirBoxReadings
    ORDER BY updated_at DESC
    LIMIT {limit};
    """
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn)


def execute_custom_sql(query_sql: str, db_path: str = DB_FILE) -> pd.DataFrame:
    """步驟 10：供教學與驗證用的自訂 SQL 查詢執行器"""
    with get_connection(db_path) as conn:
        return pd.read_sql_query(query_sql, conn)


def get_summary_statistics(db_path: str = DB_FILE) -> Dict[str, Any]:
    """計算整體的摘要統計數據"""
    sql = """
    SELECT 
        COUNT(*) AS total_records,
        COUNT(DISTINCT regionName) AS total_regions,
        MIN(dataDate) AS start_date,
        MAX(dataDate) AS end_date,
        ROUND(MIN(minT), 1) AS lowest_temp,
        ROUND(MAX(maxT), 1) AS highest_temp,
        ROUND(AVG((minT + maxT) / 2.0), 1) AS overall_avg_temp
    FROM TemperatureForecasts;
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        if row and row["total_records"] > 0:
            return dict(row)
        return {
            "total_records": 0,
            "total_regions": 0,
            "start_date": "N/A",
            "end_date": "N/A",
            "lowest_temp": 0.0,
            "highest_temp": 0.0,
            "overall_avg_temp": 0.0,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("🗄️ 步驟 3：存入 SQLite 資料庫 (data.db) 與執行驗證查詢")
    print("=" * 60)

    # 1. 初始化資料庫與資料表
    init_db()
    print("✅ 資料表 TemperatureForecasts 初始化完成！")

    # 2. 載入 weather_data.csv 或示範資料
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data.csv")
    records_to_insert = []
    if os.path.exists(csv_path):
        import pandas as pd
        csv_df = pd.read_csv(csv_path)
        records_to_insert = csv_df.to_dict(orient="records")
        print(f"📄 讀取中間產物 {csv_path} (共 {len(records_to_insert)} 筆資料)")
    else:
        import cwa_service
        records_to_insert = cwa_service.generate_sample_forecast_data("2026-04-14")
        print("📄 載入標準示範資料集 (六大分區一週數據)")

    inserted_count = insert_forecasts(records_to_insert)
    print(f"💾 成功將 {len(records_to_insert)} 筆氣溫紀錄存入 data.db (UPSERT 完成)！\n")

    # 3. 驗證查詢 ①：列出所有地區名稱
    print("🔍 驗證查詢 1：列出所有地區名稱")
    print("   SQL: SELECT DISTINCT regionName FROM TemperatureForecasts;")
    print("-" * 50)
    distinct_regs = get_distinct_regions()
    for reg in distinct_regs:
        print(f"   • {reg}")
    print("-" * 50)

    # 4. 驗證查詢 ②：查詢中部地區資料
    print("\n🔍 驗證查詢 2：查詢中部地區資料")
    print("   SQL: SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';")
    print("-" * 50)
    taichung_df = get_forecasts_by_region("中部地區")
    print(taichung_df[["dataDate", "minT", "maxT", "avgT"]].to_string(index=False))
    print("-" * 50)

    print("\n🎉 步驟 3 完成！資料庫已準備就緒。")
    print("👉 請繼續執行第四步啟動 Web App：streamlit run app.py\n")

