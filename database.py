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
    步驟 20：重複執行不重複插入 (UPSERT)
    使用 SQLite 的 ON CONFLICT(regionName, dataDate) DO UPDATE
    確保重複執行更新時直接更新 minT 與 maxT，不產生重複記錄。
    """
    if not records:
        return 0

    upsert_sql = """
    INSERT INTO TemperatureForecasts (regionName, dataDate, minT, maxT, updated_at)
    VALUES (:regionName, :dataDate, :minT, :maxT, CURRENT_TIMESTAMP)
    ON CONFLICT(regionName, dataDate) DO UPDATE SET
        minT = excluded.minT,
        maxT = excluded.maxT,
        updated_at = CURRENT_TIMESTAMP;
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(upsert_sql, records)
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
