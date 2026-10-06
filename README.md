# ⛅ Taiwan Weather Forecast 從氣象資料到互動式天氣預報應用程式

> **核心技術**：`CWA API` × `JSON` × `Python` × `SQLite` × `Streamlit`  
> **核心資料流**：資料獲取 ➔ 資料分析 ➔ 資料儲存 ➔ 資料查詢 ➔ 視覺化展示  
> **精神標語**：*用程式探索天氣，用資料看見台灣！*

---

## 📌 專案簡介 (Overview)

本專案依據 **Taiwan Weather Forecast** 課程規格完整開發，串接交通部中央氣象署 (CWA) 開放資料平台 API，經由 Python 進行階層式 JSON 資料分析與清洗，持久化儲存至本地 SQLite 資料庫 (`data.db`)，並由 Streamlit 嚴格自 SQLite 查詢資料，呈現包含六大分區最高/最低氣溫折線圖、一週資料表格以及進階衛星雲圖與 AirBox 物聯網測站地圖。

```text
[ 📡 CWA Open Data (F-D0047-091) ] ➔ [ 📄 JSON (7-day forecast) ] ➔ [ 🐍 Python (analysis & parsing) ] ➔ [ 🗄️ SQLite (data.db) ] ➔ [ 🎈 Streamlit (web app) ] ➔ [ 🌤️ Taiwan Weather Dashboard ]
```

### 🏆 核心學習指標 (Learning Outcomes)
* ✅ **學會使用 Open Data API**：串接 CWA 開放資料 API (個人授權碼 + `F-D0047-091` 一週預報)
* ✅ **掌握 JSON 資料結構分析**：深入解析多層巢狀結構 (`Locations` ➔ `Location` ➔ `WeatherElement` ➔ `最低溫度/最高溫度`)
* ✅ **建立 SQLite 資料庫**：建立 `TemperatureForecasts` 資料表與 UNIQUE 鍵 + UPSERT 更新機制
* ✅ **使用 Streamlit 製作互動式 Web App**：前端圖表與表格**嚴格由 `data.db` 查詢**，無任何前端直接外部 API 呼叫
* ✅ **培養資料處理與視覺化能力**：支援六大分區、完整 7 天預報、Plotly 雙溫走勢折線圖、Folium 全球衛星雲圖與即時雷達回波疊加

---

## 🔑 1. 個人 CWA API 授權碼配置 (Personal API Key)

本專案嚴格落實**使用個人 CWA API Key 進行實際線上抓取，不使用公用或他人金鑰，並透過環境變數保護隱私**：

* **金鑰安全性**：專案支援透過環境變數 `CWA_API_KEY` 或本地私密 `.env` 檔案載入（`.env` 已加入 `.gitignore` 排除，**金鑰絕不上傳至公開儲存庫**）。
* **資料集代碼**：`F-D0047-091`（臺灣各縣市鄉鎮未來1週逐12小時天氣預報，參照 [CWA 開放資料清單 datalist](https://opendata.cwa.gov.tw/devManual/datalist)）
* **環境變數設定方式**：
  * **Windows PowerShell**：
    ```powershell
    [System.Environment]::SetEnvironmentVariable('CWA_API_KEY', '您的CWA金鑰', 'User')
    $env:CWA_API_KEY="您的CWA金鑰"
    ```
  * **Linux / macOS**：
    ```bash
    export CWA_API_KEY="您的CWA金鑰"
    ```
  * **或使用本地 `.env` 檔案**：
    在專案根目錄建立 `.env` 檔案：
    ```text
    CWA_API_KEY=您的CWA金鑰
    ```
* **介面支援**：在 Streamlit「🔄 資料同步與 CWA API」控制台中，亦可自由檢視、輸入個人金鑰並以密碼遮罩保護。

---

## 🗄️ 2. SQLite 資料架構 (Strict SQLite Architecture)

**Web App 嚴格遵循微課程規範架構**：
1. **前端圖表與表格由 `data.db` 讀取**：Streamlit 應用程式中的所有統計指標 (KPI)、下拉選單地區資料、MaxT/MinT 折線圖、一週資料表及全台六大分區矩陣，**100% 透過 SQL 語法向 `data.db` 查詢**（`database.get_forecasts_by_region()`、`database.get_all_forecasts()`）。
2. **禁止 Streamlit 前端直接向外部 API 發出非同步請求繪圖**，確保資料庫持久化架構的純粹性與離線可讀性。

### SQLite Schema (`TemperatureForecasts`)
```sql
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    minT REAL NOT NULL,
    maxT REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regionName, dataDate)
);
```

---

## 📊 3. 資料正確性驗證 (Data Accuracy)

### 六大分區與完整一週 (7天) 氣溫數據
經由 CWA API (`F-D0047-091`) 真實線上抓取並寫入 `data.db`：

| 分區名稱 | 涵蓋範圍 | 7天最低溫 (MinT) | 7天最高溫 (MaxT) | 今日 10/06 氣溫 | 狀態 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **北部地區** | 基隆市、臺北市、新北市、桃園市、新竹縣市、苗栗縣 | 21.0 ~ 22.0°C | 25.0 ~ 32.0°C | 21.0°C ~ 25.0°C | ✅ 正確驗證 |
| **中部地區** | 臺中市、彰化縣、南投縣、雲林縣、嘉義縣市 | 22.0 ~ 24.0°C | 29.0 ~ 33.0°C | 23.0°C ~ **29.0°C** | ✅ 正確驗證 |
| **南部地區** | 臺南市、高雄市、屏東縣、澎湖縣 | 24.0 ~ 25.0°C | 31.0 ~ 33.0°C | 24.0°C ~ 31.5°C | ✅ 正確驗證 |
| **東北部地區** | 宜蘭縣與東北角地區 | 21.0 ~ 24.0°C | 23.0 ~ 30.0°C | 21.0°C ~ 23.0°C | ✅ 正確驗證 |
| **東部地區** | 花蓮縣地區 | 22.0 ~ 24.0°C | 25.0 ~ 30.0°C | 22.0°C ~ 25.0°C | ✅ 正確驗證 |
| **東南部地區** | 臺東縣地區 | 23.5 ~ 25.0°C | 28.5 ~ 31.0°C | 23.5°C ~ 28.5°C | ✅ 正確驗證 |

> 📌 **驗證說明**：
> 1. 今日 10/06 臺中 / 中部地區白天實測最高溫為 **29.0°C**，已精確納入資料庫與圖表起點。
> 2. 修正了早期版本因 18:00 後僅抓取晚間時段或將 3000 公尺高山測站誤納的偏差，現已全面對齊中央氣象署生活天氣預報真實數值。

---

## 🗺️ 五大核心模組規格與實作對應 (Modules)

### 1️⃣ 模組 1：取得 CWA API 資料 (20%)
* **檔案**：[`fetch_weather.py`](file:///c:/Users/user/Desktop/碩士/應用物聯網作業/fetch_weather.py)
* **規格**：呼叫 CWA API (`F-D0047-091`)，使用 `json.dumps` 觀察結構，儲存為 `cwa_weather_raw.json`。

### 2️⃣ 模組 2：分析 JSON，提取氣溫資料 (20%)
* **檔案**：[`parse_weather.py`](file:///c:/Users/user/Desktop/碩士/應用物聯網作業/parse_weather.py)
* **規格**：解析 `Locations` ➔ `Location` ➔ `WeatherElement`，產出清洗之中間產物 `weather_data.csv`。

### 3️⃣ 模組 3：存入 SQLite 資料庫 (20%)
* **檔案**：[`database.py`](file:///c:/Users/user/Desktop/碩士/應用物聯網作業/database.py)
* **規格**：寫入 `data.db`，使用 `ON CONFLICT DO UPDATE` 防止重複插入，並提供標準 SQL 驗證查詢。

### 4️⃣ 模組 4：Streamlit 氣溫預報 Web App (40%)
* **檔案**：[`app.py`](file:///c:/Users/user/Desktop/碩士/應用物聯網作業/app.py)
* **規格**：
  * 下拉選單選擇六大地區 (`st.selectbox`)
  * 嚴格由 SQLite 查詢 (`database.get_forecasts_by_region()`)
  * Plotly 繪製 MaxT (紅線) 與 MinT (藍線) 折線圖
  * 一週 7 天氣象資料表與 CSV 匯出功能
  * 全台六大分區綜合對比矩陣與趨勢圖

### 5️⃣ 模組 5：進階：台灣地圖視覺化 (加分功能)
* **檔案**：[`app.py`](file:///c:/Users/user/Desktop/碩士/應用物聯網作業/app.py) / [`index.html`](file:///c:/Users/user/Desktop/碩士/應用物聯網作業/index.html)
* **規格**：
  * Esri World Imagery 全球衛星雲圖底圖
  * RainViewer 即時衛星雷達回波圖層疊加
  * 全台 340+ 氣象測站與 150+ AirBox 物聯網節點互動 Popup
  * 溫度色階標準標記 (<20°C 藍、20-25°C 綠、25-30°C 黃、>30°C 紅)

---

## 📂 專案檔案結構 (Project Structure)

```text
weather_app/
├── fetch_weather.py     # [模組 1] 呼叫 CWA API 取得原始預報 JSON (個人金鑰)
├── parse_weather.py     # [模組 2] 分析 JSON 階層結構，提取六大分區 MinT 與 MaxT
├── database.py          # [模組 3] 建立 SQLite 資料庫 (data.db) 與執行驗證查詢
├── app.py               # [模組 4 & 5] Streamlit 主程式 (嚴格由 SQLite 讀取)
├── cwa_service.py       # CWA API 串接、憑證防護與解析核心服務
├── iot_service.py       # 全台 340+ 即時測站與 AirBox IoT 感測節點服務
├── data.db              # SQLite 資料庫本體 (TemperatureForecasts)
├── weather_data.csv     # [中間產物] 清洗後之六大分區一週氣溫 CSV
├── cwa_weather_raw.json # [原始產物] CWA 官方回傳之原始 JSON (1.7 MB)
├── index.html           # 獨立 Web 儀表板 (含衛星地圖與真實 CWA 預報)
├── requirements.txt     # Python 相依套件清單
├── run_app.bat          # Windows 一鍵啟動指令檔
├── push_to_github.bat   # GitHub 一鍵推送指令檔
└── README.md            # 專案說明文件
```

---

## 🚀 執行與驗證步驟 (Step-by-Step Guide)

### 步驟 1：安裝相依套件
```bash
pip install -r requirements.txt
```

### 步驟 2：執行完整資料管線 (Pipeline)
依序執行線上抓取、JSON 分析與存入資料庫：
```bash
# 1. 使用個人金鑰抓取 CWA 最新預報
python fetch_weather.py

# 2. 分析 JSON 並輸出 weather_data.csv
python parse_weather.py

# 3. 存入 SQLite data.db 並執行驗證查詢
python database.py
```

### 步驟 3：啟動 Streamlit Web App
```bash
streamlit run app.py
```
或於 Windows 檔案總管中雙擊 [`run_app.bat`](file:///c:/Users/user/Desktop/碩士/應用物聯網作業/run_app.bat)。

---

## ✅ 作業規範檢核清單 (Compliance Checklist)

- [x] **個人 CWA API Key**：設定於環境變數 `CWA_API_KEY` 或本地 `.env` 檔案中，不使用公用金鑰且不公開金鑰字串。
- [x] **Streamlit 嚴格由 SQLite 讀取**：前端圖表與表格 100% 由 `data.db` 查詢，前端無外部 API 呼叫。
- [x] **六大分區完整正確**：北部、中部、南部、東北部、東部、東南部資料完整。
- [x] **一週 7 天資料完整**：日期連續、MinT 與 MaxT 合理且符合秋季實際氣候。
- [x] **進階台灣地圖實作**：全球衛星雲圖 + 雷達回波疊加 + 測站氣溫彈出資訊。