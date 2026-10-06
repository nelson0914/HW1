# ⛅ HW10 Taiwan Weather Forecast 從氣象資料到互動式天氣預報應用程式

> **核心技術**：`CWA API` × `JSON` × `Python` × `SQLite` × `Streamlit`  
> **核心資料流**：資料獲取 ➔ 資料分析 ➔ 資料儲存 ➔ 資料查詢 ➔ 視覺化展示  
> **精神標語**：*用程式探索天氣，用資料看見台灣！*

---

## 📌 專案簡介 (Overview)

本專案依據 **HW10 Taiwan Weather Forecast** 規格完整開發，串接交通部中央氣象署 (CWA) 開放資料 API，經由 Python 進行階層式 JSON 分析清洗，持久化儲存至 SQLite 資料庫，並使用 Streamlit 建立具備互動式折線圖、7 天預報表格與 Folium 台灣地圖四段溫度色彩階層之氣象儀表板。

```text
[ 📡 CWA Open Data (F-A0010-001) ] ➔ [ 📄 JSON (7-day forecast) ] ➔ [ 🐍 Python (analysis & parsing) ] ➔ [ 🗄️ SQLite (data.db) ] ➔ [ 🎈 Streamlit (web app) ] ➔ [ 🌤️ Taiwan Weather Dashboard ]
```

### 🏆 核心學習指標 (Learning Outcomes)
* ✅ 學會使用 Open Data API
* ✅ 掌握 JSON 資料結構分析
* ✅ 建立 SQLite 資料庫
* ✅ 使用 Streamlit 製作互動式 Web App
* ✅ 培養資料處理與視覺化能力

---

## 🗺️ 五大核心模組規格 (Modules)

### 1️⃣ 模組 1：取得 CWA API 資料 (20%)
* **目標**：使用 CWA API 取得台灣六大區域一週天氣預報 (必須使用 JSON 格式)。
* **六大區域**：
  * **北部地區**、**中部地區**、**南部地區**、**東北部地區**、**東部地區**、**東南部地區**
* **主要步驟**：
  1. 使用 `requests` 呼叫 CWA API (`F-A0010-001` 或 `F-D0047-091`)
  2. 使用 `json.dumps` 觀察回傳的 JSON 資料結構
  3. 確認資料取得成功並儲存為原始檔
* **評分項目**：取得資料 10% ｜ 觀察JSON 5% ｜ 程式品質 5%

### 2️⃣ 模組 2：分析 JSON，提取氣溫資料 (20%)
* **目標**：分析 JSON 結構，找出並提取每日最高與最低氣溫 (Region 在資料中通常以 Location 表示)。
* **分析重點 (JSON 巢狀結構)**：
  ```text
  JSON
  └── records
      └── locations
          └── location[] (地區)
              └── weatherElement[] (天氣要素)
                  └── time[] (預報日期)
                      ├── elementName: MinT (最低溫)
                      └── elementName: MaxT (最高溫)
  ```
* **提取結果範例**：
  | regionName | dataDate | mint | maxt |
  | :--- | :---: | :---: | :---: |
  | 北部地區 | 2026-04-14 | 18.0 | 26.0 |
  | 中部地區 | 2026-04-14 | 20.0 | 30.0 |
  | 南部地區 | 2026-04-14 | 22.0 | 31.0 |
* **評分項目**：提取正確 10% ｜ 觀察資料 5% ｜ 程式品質 5%

### 3️⃣ 模組 3：存入 SQLite 資料庫 (20%)
* **目標**：將氣溫資料儲存到 SQLite 資料庫 (`data.db`)。
* **資料庫設計**：
  ```sql
  CREATE TABLE TemperatureForecasts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      regionName TEXT NOT NULL,
      dataDate TEXT NOT NULL,
      mint REAL NOT NULL,
      maxt REAL NOT NULL,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(regionName, dataDate)
  );
  ```
* **驗證查詢**：
  1. 列出所有地區名稱：
     ```sql
     SELECT DISTINCT regionName FROM TemperatureForecasts;
     ```
  2. 查詢中部地區資料：
     ```sql
     SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區';
     ```
* **評分項目**：儲存資料 10% ｜ 查詢驗證 5% ｜ 程式品質 5%

### 4️⃣ 模組 4：Streamlit 氣溫預報 Web App (40%)
* **目標**：建立互動式 Web App，從 SQLite 查詢資料，提供下拉選單，顯示一週氣溫的折線圖與表格。
* **功能需求**：
  1. 下拉選單選擇地區 (`st.selectbox`)
  2. 使用 SQL 從 SQLite (`data.db`) 查詢資料 (`pd.read_sql_query`)
  3. 顯示最高溫 (`MaxT` 紅線) 與最低溫 (`MinT` 藍線) 折線圖
  4. 顯示一週 (7 天) 資料表格與 CSV 下載
* **評分項目**：下拉選單 10% ｜ 折線圖與表格 15% ｜ SQLite 查詢 10% ｜ 程式品質 5%

### 5️⃣ 模組 5：進階：台灣地圖視覺化 (Optional 加分)
* **目標**：製作互動式台灣地圖，顯示各區當日平均溫度 (使用 Folium + Streamlit)。
* **依平均溫度設定顏色**：
  * 🔵 **< 20°C**：藍色 (涼爽)
  * 🟢 **20 - 25°C**：綠色 (舒適)
  * 🟡 **25 - 30°C**：黃色 (溫暖)
  * 🔴 **> 30°C**：紅色 (炎熱)
* **地圖標示與 Popup**：標示六大分區，點擊跳出詳細氣象數值卡片。

---

## 📂 專案檔案結構 (Project Structure)

完全依循 HW10 官方標準目錄設計：

```text
HW10_weather/
├── fetch_weather.py   # [模組 1] 呼叫 CWA API 取得原始預報 JSON
├── parse_weather.py   # [模組 2] 分析 JSON 階層結構，提取 MinT 與 MaxT
├── database.py        # [模組 3] 建立 SQLite 資料庫與執行驗證查詢
├── app.py             # [模組 4 & 5] Streamlit 互動預報與 Folium 地圖主程式
├── data.db            # SQLite 資料庫 (儲存 TemperatureForecasts 資料表)
├── weather_data.csv   # [中間產物] 清洗後之一週六大分區氣溫數值
├── cwa_service.py     # CWA API 輔助服務與基準數據生成
├── iot_service.py     # 測站觀測與物聯網輔助服務
├── requirements.txt   # 相依套件清單
├── run_app.bat        # Windows 一鍵啟動指令檔
└── README.md          # 專案說明文件
```

---

## 🚀 執行方式 (Getting Started)

### 步驟 1：建立虛擬環境 (建議)
```bash
python -m venv venv
# Windows 啟動虛擬環境:
venv\Scripts\activate
# Mac / Linux 啟動虛擬環境:
source venv/bin/activate
```

### 步驟 2：安裝相依套件
```bash
pip install -r requirements.txt
```

### 步驟 3：執行資料處理 (一次即可)
依序執行資料擷取、解析與資料庫寫入：
```bash
# 1. 取得 CWA API 原始資料
python fetch_weather.py

# 2. 解析 JSON 並產出 weather_data.csv
python parse_weather.py

# 3. 存入 SQLite (data.db) 並執行 SQL 查詢驗證
python database.py
```

### 步驟 4：啟動 Web App
```bash
streamlit run app.py
```
> 或在 Windows 環境下直接雙擊執行 `run_app.bat`。

---

## ⚠️ 重要注意事項 (Important Notes)

1. **使用自己的 CWA API Key**：執行實際線上抓取時，請於環境變數 `CWA_API_KEY` 或於介面中輸入個人金鑰，不能使用老師提供的金鑰繳交。
2. **Streamlit 必須從 SQLite 查詢資料**：Web App 嚴格遵循架構，前端圖表與表格由 `data.db` 讀取，不可直接在 Streamlit 前端呼叫外部 API。
3. **確保六個地區的資料都正確**：包含北部、中部、南部、東北部、東部、東南部。
4. **表格與圖表需顯示一週 (7天) 資料**。
5. **進階的台灣地圖為加分功能**：已完整實作於儀表板右側，支援即時切換預報日期與彈出氣溫資訊。

---

💡 *用程式連結真實世界，讓資料說出天氣的故事！*