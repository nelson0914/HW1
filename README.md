# 🌤️ Taiwan Weather & IoT Forecast 互動式氣象與物聯網預報系統

> **碩士班 應用物聯網作業 | AI 創新微課程實作專案**  
> **核心技術**：`CWA API` × `JSON` × `Python` × `SQLite` × `Streamlit` × `Folium` × `Edimax AirBox IoT`

---

## 📌 專案簡介 (Overview)

本專案依據 **「AI 創新微課程 Taiwan Weather Forecast：從氣象資料到互動式天氣預報」** 的 24 步驟完整架構進行開發，結合中央氣象署 (CWA) 開放資料與台灣物聯網 (IoT) 即時環境感測大數據，建構全方位互動式氣象預報儀表板。

### 🌟 核心特色

1. **五大分區一週氣溫趨勢分析**：
   - 支援 北部、中部、南部、東北部、東南部 等地區切換。
   - 呈現最高氣溫 (MaxT) 與最低氣溫 (MinT) 折線圖、日夜溫差區間帶，以及資料庫詳細表格。
   - 支援一鍵匯出 CSV 報表。
2. **台灣互動式地圖視覺化 (Folium)**：
   - 遵照微課程標準四段溫度色彩階層：
     - `< 20°C`：藍色 (低溫/涼爽)
     - `20 - 25°C`：綠色 (舒適氣溫)
     - `25 - 30°C`：黃色/橘色 (溫暖微熱)
     - `> 30°C`：紅色 (高溫炎熱)
   - 支援日期的互動切換與 Marker / Circle 點擊彈出視窗 (Popup)。
3. **雙即時資料源整合**：
   - 📡 **台灣即時氣象地圖 ([taiwan-weather-map.vercel.app](https://taiwan-weather-map.vercel.app/))**：即時取得全台 340+ 座自動氣象站的高頻觀測數值。
   - 🍃 **Edimax AirBox 台灣物聯網空氣盒子 ([airbox.edimaxcloud.com](https://airbox.edimaxcloud.com/))**：結合中研院資訊所 (IIS-NRL) 與訊舟科技開放端點，即時呈現全台校園 IoT 感測節點之溫度、濕度與 PM2.5 空品狀況。
4. **SQLite 關聯式資料庫持久化**：
   - 資料表 `TemperatureForecasts` 與 `AirBoxReadings`。
   - 內建 SQL 查詢與驗證沙盒 (支援執行 `SELECT DISTINCT regionName` 等驗證語法)。
   - 支援 UPSERT 重複執行不重複插入機制。

---

## ⚖️ 資料來源合法性與安全防護聲明 (Legal & Open Data Compliance)

為確保本網站完全符合台灣與國際網路法規，杜絕「未授權爬蟲」、「DDoS 伺服器超載」或「侵權」疑慮，本系統採用最高標準之合法合規防護：

1. **依據合法開放資料授權條款**：
   - **中央氣象署 (CWA) 氣象資料**：依據中華民國「**政府資料開放授權條款 (Open Government Data License, OGDL-Taiwan) 第一號**」，開放學術研究、個人及商業合法重製、改作與散布，本專案依規定完整標明出處。
   - **Edimax AirBox / LASS 物聯網開放資料**：訊舟科技 (Edimax) 與中央研究院資訊科技創新研究中心 (IIS-NRL) 合作推動之社群開放資料，採用「**創用 CC 姓名標示-相同方式分享 (CC-BY-SA 4.0)**」授權，供物聯網教學與研究使用。
2. **智慧防洪快取 (Rate Limiting & In-Memory Caching)**：
   - 系統核心內建 **300 秒 (5 分鐘) 的 TTL 快取機制**。
   - 使用者瀏覽或點擊時均由快取提供，嚴格限制對外部網站的連線頻率，絕無高頻密集輪詢 (No DDOS / No hammering)。
3. **透明學術 User-Agent 標頭**：
   - 發送請求時明確表明身分：`Taiwan-IoT-Academic-Course-Project/1.0 (Master Degree IoT Coursework)`，身分透明且遵循網路禮節。
4. **無機敏個資與會員資料**：
   - 僅讀取公開大氣物理數值 (氣溫、濕度、PM2.5、風速)，絕不涉及任何個人隱私或會員帳號資料。

---

## 🗺️ 專案架構與微課程 24 步驟對應

| 步驟編號 | 學習主題 | 本專案實作模組與功能 |
| :---: | :--- | :--- |
| **01~02** | 課程介紹與台灣天氣生活 | 儀表板設計理念、物聯網生活應用與學習地圖導覽頁 |
| **03~04** | CWA Open Data 與 API 取得 | `cwa_service.py` 封裝 Requests 取得 JSON 預報資料 |
| **05~06** | JSON 結構解析與 MinT/MaxT 提取 | 解析 locations、weatherElement 提取氣溫數值 |
| **07** | 資料整理與預覽 | 使用 Pandas 結構化清洗為乾淨的 DataFrame 表格 |
| **08~09** | SQLite 資料庫與 Schema 設計 | `database.py` 建立 `data.db` 與 `TemperatureForecasts` 資料表 |
| **10** | 查詢資料驗證 | 內建 SQL 查詢沙盒，支援驗證 DISTINCT 與 WHERE 語法 |
| **11~12** | Streamlit 入門與 SQL 讀取 | `app.py` 串接 `pd.read_sql_query` 即時讀取資料庫 |
| **13** | 下拉選單選擇地區 | `st.selectbox` 互動篩選全台各大區域 |
| **14** | 繪製折線圖 | Plotly 互動式折線圖 (MaxT 紅線、MinT 藍線、溫差填色) |
| **15** | 顯示資料表格 | 結構化 Dataframe 即時呈現一週數值，支援下載 CSV |
| **16** | 整合 Web App 介面 | 響應式雙欄儀表板佈局、KPI 卡片整合 |
| **17** | 進階：台灣地圖視覺化 | Folium 台灣地圖，四段平均溫度色彩階層標記 |
| **18** | 選擇日期顯示地圖 | 日期選擇器、地圖 Marker 點擊跳出氣候詳細資訊 Popup |
| **19** | 完整成果展示 | Taiwan Weather Dashboard 綜合成果展示 |
| **20** | 程式碼品質與優化 | 模組化分工、UPSERT 防重複插入、例外處理機制 |
| **21** | 專案上傳至 GitHub | Git 版本控制、規範 .gitignore 與 README |
| **22~24** | 延伸應用與未來探索 | 整合 Edimax AirBox 台灣校園物聯網環境感測數據 |

---

## 📂 檔案目錄結構

```text
應用物聯網作業/
├── app.py              # Streamlit 主程式 (儀表板、地圖視覺化、UI 控制)
├── database.py         # SQLite 資料庫操作模組 (Schema, 連線, UPSERT, 查詢)
├── cwa_service.py      # 中央氣象署 (CWA) API 擷取、JSON 解析與示範資料生成
├── iot_service.py      # 台灣氣象地圖與 Edimax AirBox 開放資料同步模組 (含合規快取)
├── data.db             # SQLite 資料庫本體 (自動初始化)
├── requirements.txt    # Python 相依套件清單
├── run_app.bat         # Windows 一鍵啟動批次檔
├── .gitignore          # Git 忽略檔案設定
└── README.md           # 完整專案說明文件
```

---

## 🚀 快速開始 (Quick Start)

### 1. 安裝相依套件

請確保已安裝 Python 3.10 以上版本，並於終端機執行：

```bash
pip install -r requirements.txt
```

### 2. 啟動 Web 應用程式

#### 方式一：使用 Windows 一鍵啟動 (推薦)
直接雙擊執行目錄下的 `run_app.bat` 檔案。

#### 方式二：使用指令啟動
```bash
streamlit run app.py
```

啟動後，瀏覽器將自動開啟：`http://localhost:8501`。

---

## 💻 系統截圖與操作說明

1. **🌤️ 天氣預報儀表板**：
   - 頂部 KPI 卡片顯示全島平均溫、最高溫與最低溫。
   - 左側可切換地區查看氣溫走勢折線圖與預報表格。
   - 右側可切換「微課程五大分區」、「台灣氣象地圖 340+ 測站」或「Edimax AirBox 校園物聯網節點」地圖圖層。
2. **🌐 氣象與物聯網資料同步**：
   - 支援一鍵連線更新外部開放資料至 SQLite 本地資料庫。
   - 亦可輸入使用者自訂之 API 網址進行擴充。
3. **🔍 SQL 查詢與資料驗證**：
   - 內建教學用 SQL 查詢範本，可即時執行並驗證資料庫資料。
4. **⚖️ 開放資料授權與合法性說明**：
   - 完整標明資料授權來源與系統安全機制。

---

## 📜 授權與版權聲明 (Credits)

- **主辦課程**：AI 創新微課程 Taiwan Weather Forecast
- **資料來源**：
  - 中華民國交通部中央氣象署 (Central Weather Administration, CWA)
  - 台灣即時氣象地圖 (Taiwan Weather Map)
  - 訊舟科技 (Edimax) AirBox × 中央研究院資訊科學研究所 (IIS-NRL) LASS 開放資料社群
- **著作權與使用條款**：
  - 本專案程式碼基於 MIT License 開源。
  - 氣象資料依「政府資料開放授權條款 (OGDL) 第一號」使用。
  - 感測器資料依「創用 CC 姓名標示-相同方式分享 (CC-BY-SA 4.0)」使用。
#   H W 1  
 #   H W 1  
 #   H W 1  
 