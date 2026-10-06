"""
app.py - HW10 Taiwan Weather Forecast 從氣象資料到互動式天氣預報應用程式
核心技術：CWA API × JSON × Python × SQLite × Streamlit
資料流：資料獲取 · 資料分析 · 資料儲存 · 資料查詢 · 視覺化展示
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime
import json

# 匯入後端模組
import database
import cwa_service
import iot_service

# -----------------------------------------------------------------------------
# 頁面基本配置 (Streamlit Page Config)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="HW10 Taiwan Weather Forecast | 互動式天氣預報應用程式",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 全域 CSS 美化 (HW10 經典主題、精緻卡片、圓角陰影與字體)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* 頂部主視覺 Banner (對應海報 Header) */
    .hw10-hero-banner {
        background: linear-gradient(135deg, #092042 0%, #103b7b 45%, #0284c7 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 16px;
        margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(10, 35, 75, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.18);
        position: relative;
        overflow: hidden;
    }
    .hw10-hero-banner::after {
        content: "🌤️";
        position: absolute;
        right: 20px;
        top: -15px;
        font-size: 8rem;
        opacity: 0.12;
        pointer-events: none;
    }
    .banner-top-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 15px;
    }
    .banner-title-left {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .banner-title-text {
        font-size: 2.1rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.15;
    }
    .banner-tech-stack {
        font-size: 1.05rem;
        color: #fde047;
        font-weight: 700;
        margin-top: 5px;
        letter-spacing: 0.5px;
    }
    .banner-title-right {
        text-align: right;
    }
    .banner-subhead-zh {
        font-size: 1.45rem;
        font-weight: 800;
        color: #ffffff;
    }
    .banner-substeps {
        font-size: 0.92rem;
        color: #bae6fd;
        margin-top: 4px;
        font-weight: 500;
    }
    .banner-slogan {
        font-size: 0.85rem;
        color: #e0f2fe;
        margin-top: 4px;
        opacity: 0.9;
    }

    /* 流程架構指示條 (海報 Architecture Flow Bar) */
    .hw10-flow-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 14px 20px;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
        flex-wrap: wrap;
        gap: 10px;
    }
    .flow-steps {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }
    .flow-node {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.84rem;
        font-weight: 700;
        color: #1e293b;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 100px;
        text-align: center;
    }
    .flow-node small {
        font-size: 0.72rem;
        color: #64748b;
        font-weight: normal;
    }
    .flow-arrow {
        color: #0284c7;
        font-weight: 900;
        font-size: 1.1rem;
    }
    .goals-badge-box {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 0.78rem;
        color: #166534;
        line-height: 1.45;
        max-width: 320px;
    }

    /* 廣播即時跑馬燈橫幅 (Weather Broadcast Ribbon) */
    .broadcast-ribbon {
        background: linear-gradient(90deg, #eff6ff 0%, #f0fdf4 100%);
        border-left: 5px solid #0284c7;
        border-radius: 8px;
        padding: 10px 18px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.9rem;
        color: #0f172a;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }

    /* 核心指標卡片 (Metric Cards) */
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 14px 16px;
        border: 1px solid #e2e8f0;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.03);
        transition: transform 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    .metric-title {
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .metric-num {
        font-size: 1.7rem;
        font-weight: 900;
        line-height: 1.1;
    }
    .metric-desc {
        font-size: 0.74rem;
        color: #94a3b8;
        margin-top: 3px;
    }

    /* 海報 5 個模組卡片樣式 */
    .module-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 18px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.03);
        height: 100%;
    }
    .module-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
    }
    .module-badge {
        background: #0284c7;
        color: white;
        font-weight: 800;
        font-size: 0.9rem;
        padding: 3px 10px;
        border-radius: 6px;
    }
    .module-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0f172a;
    }
    .module-score {
        font-size: 0.95rem;
        color: #0284c7;
        font-weight: 700;
    }

    /* 步驟 17 溫度色階圖例 */
    .temp-legend-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 14px;
        margin: 10px 0;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
    }

    /* 區域標籤 Chips */
    .region-chip {
        display: inline-block;
        background: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-right: 6px;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 資料庫初始化與資料就緒檢查 (HW10 規範)
# @st.cache_resource 確保 Streamlit Cloud 冷啟動時只初始化一次
# -----------------------------------------------------------------------------
@st.cache_resource
def _init_database():
    """初始化資料庫並載入 HW10 基準預報資料 (僅執行一次)"""
    database.init_db()
    regions = database.get_distinct_regions()
    if not regions:
        sample_records = cwa_service.generate_sample_forecast_data("2026-04-14")
        database.insert_forecasts(sample_records)
    return True

_init_database()


# -----------------------------------------------------------------------------
# 輔助函式：HW10 模組 5 溫度色彩標準
# -----------------------------------------------------------------------------
def get_temperature_color(avg_temp: float) -> str:
    """
    HW10 模組 5 色彩規範：
      < 20°C: 藍色 (#2196F3)
      20 - 25°C: 綠色 (#4CAF50)
      25 - 30°C: 黃色 (#FFC107)
      > 30°C: 紅色 (#F44336)
    """
    if avg_temp < 20.0:
        return "#2196F3"
    elif avg_temp <= 25.0:
        return "#4CAF50"
    elif avg_temp <= 30.0:
        return "#FFC107"
    else:
        return "#F44336"


def get_pm25_color(pm25: float) -> str:
    """空氣品質 PM2.5 顏色標準"""
    if pm25 <= 15.4:
        return "#4CAF50"
    elif pm25 <= 35.4:
        return "#FFEB3B"
    elif pm25 <= 54.4:
        return "#FF9800"
    elif pm25 <= 150.4:
        return "#F44336"
    else:
        return "#9C27B0"


# -----------------------------------------------------------------------------
# 側邊欄控制台 (Sidebar Controls) - 遵照需求移除開放授權與24步導覽
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/sun.png", width=75)
    st.title("HW10 控制台")
    st.caption("CWA API × JSON × SQLite × Streamlit")
    st.markdown("---")

    menu_choice = st.radio(
        "選擇功能分頁：",
        [
            "🌤️ 氣溫預報 Web App (Live Dashboard)",
            "📋 HW10 課程專案架構全覽 (Assignment Guide)",
            "🔍 SQLite 資料庫與 SQL 驗證 (Database Sandbox)",
            "🔄 資料同步與 CWA API (Data Sync)"
        ],
        index=0
    )

    st.markdown("---")
    st.subheader("⚡ 快速資料操作")

    if st.button("🔄 載入 HW10 標準示範預報 (2026-04-14)", use_container_width=True):
        samples = cwa_service.generate_sample_forecast_data("2026-04-14")
        database.insert_forecasts(samples)
        st.success("✅ 已同步載入 HW10 基準一週預報資料！")
        st.rerun()

    if st.button("📡 同步 全台即時觀測站 (340+站)", use_container_width=True):
        with st.spinner("正在連線更新全台測站觀測數據..."):
            ok, msg, reg_data, _ = iot_service.fetch_taiwan_weather_map_data(force_refresh=True)
            if ok and reg_data:
                database.insert_forecasts(reg_data)
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")
    st.subheader("📊 SQLite 即時統計")
    stats = database.get_summary_statistics()
    st.write(f"• **資料庫本體**：`data.db`")
    st.write(f"• **預報資料表記錄**：`{stats.get('total_records', 0)}` 筆")
    st.write(f"• **涵蓋六大分區**：`{stats.get('total_regions', 0)}` 區")
    st.write(f"• **日期區間**：`{stats.get('start_date', 'N/A')}` ~ `{stats.get('end_date', 'N/A')}`")


# -----------------------------------------------------------------------------
# 頂部主視覺橫幅 (HW10 Hero Banner - 完美對應海報 Header)
# -----------------------------------------------------------------------------
st.markdown("""
<div class="hw10-hero-banner">
    <div class="banner-top-row">
        <div class="banner-title-left">
            <span style="font-size: 2.8rem;">🌤️</span>
            <div>
                <div class="banner-title-text">HW10 Taiwan Weather Forecast</div>
                <div class="banner-tech-stack">CWA API × JSON × Python × SQLite × Streamlit</div>
            </div>
        </div>
        <div class="banner-title-right">
            <div class="banner-subhead-zh">從氣象資料到互動式天氣預報應用程式</div>
            <div class="banner-substeps">資料獲取 · 資料分析 · 資料儲存 · 資料查詢 · 視覺化展示</div>
            <div class="banner-slogan">🏙️ 用程式探索天氣 · 用資料看見台灣</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 系統架構流程與學習重點條 (對應海報流程圖與右側學習重點)
# -----------------------------------------------------------------------------
st.markdown("""
<div class="hw10-flow-container">
    <div class="flow-steps">
        <div class="flow-node">
            <span>📡 CWA Open Data</span>
            <small>F-A0010-001</small>
        </div>
        <span class="flow-arrow">➔</span>
        <div class="flow-node">
            <span>📄 JSON</span>
            <small>7-day forecast</small>
        </div>
        <span class="flow-arrow">➔</span>
        <div class="flow-node">
            <span>🐍 Python</span>
            <small>analysis & parsing</small>
        </div>
        <span class="flow-arrow">➔</span>
        <div class="flow-node">
            <span>🗄️ SQLite</span>
            <small>data.db</small>
        </div>
        <span class="flow-arrow">➔</span>
        <div class="flow-node">
            <span>🎈 Streamlit</span>
            <small>web app</small>
        </div>
        <span class="flow-arrow">➔</span>
        <div class="flow-node" style="background:#e0f2fe; border-color:#38bdf8;">
            <span style="color:#0369a1;">🌤️ Weather App</span>
            <small style="color:#0284c7;">Taiwan Dashboard</small>
        </div>
    </div>
    <div class="goals-badge-box">
        <b style="color:#15803d;">🏆 核心學習指標 (Learning Outcomes)：</b><br>
        ✓ 學會使用 Open Data API &nbsp; ✓ 掌握 JSON 資料結構分析<br>
        ✓ 建立 SQLite 資料庫 &nbsp; ✓ 使用 Streamlit 製作互動式 Web App<br>
        ✓ 培養資料處理與視覺化能力
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# 分頁 1：🌤️ 氣溫預報 Web App (Dashboard - 對應海報模組 4 & 5)
# =============================================================================
if menu_choice == "🌤️ 氣溫預報 Web App (Live Dashboard)":

    # 即時氣象廣播與 KPI 指標條 (融入 CWA Temperature Broadcast 概念)
    stats = database.get_summary_statistics()
    overall_avg = stats.get('overall_avg_temp', 25.0)
    highest_val = stats.get('highest_temp', 32.0)
    lowest_val = stats.get('lowest_temp', 18.0)
    diff_val = round(highest_val - lowest_val, 1)

    # 廣播跑馬燈
    st.markdown(f"""
    <div class="broadcast-ribbon">
        <div>
            📢 <b>全台氣象廣播 (Broadcast)</b>：
            預報期間全島最高氣溫高達 <b>{highest_val}°C</b>，最低氣溫為 <b>{lowest_val}°C</b>，六大分區平均氣溫約 <b>{overall_avg}°C</b>。建議外出適時補充水分，並留意早晚溫差變化。
        </div>
        <div style="font-size: 0.8rem; color: #64748b;">
            資料來源：CWA OpenData ｜ 本地資料庫：data.db
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 頂部四大 KPI 指標卡片
    kp1, kp2, kp3, kp4 = st.columns(4)
    with kp1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">全島預測平均溫</div>
            <div class="metric-num" style="color: #0284c7;">{overall_avg}°C</div>
            <div class="metric-desc">六大分區平均氣溫</div>
        </div>
        """, unsafe_allow_html=True)
    with kp2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">全島最高溫 (MaxT)</div>
            <div class="metric-num" style="color: #e11d48;">{highest_val}°C</div>
            <div class="metric-desc">一週預報最高紀錄</div>
        </div>
        """, unsafe_allow_html=True)
    with kp3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">全島最低溫 (MinT)</div>
            <div class="metric-num" style="color: #2563eb;">{lowest_val}°C</div>
            <div class="metric-desc">一週預報最低紀錄</div>
        </div>
        """, unsafe_allow_html=True)
    with kp4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">全島溫差幅度</div>
            <div class="metric-num" style="color: #f59e0b;">{diff_val}°C</div>
            <div class="metric-desc">預報極值溫差</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 左右雙欄佈局：左側模組 4 (Streamlit 氣溫預報 Web App 40%)，右側模組 5 (進階：台灣地圖視覺化)
    col_left, col_right = st.columns([1.08, 0.92], gap="large")

    # -------------------------------------------------------------------------
    # 左欄：模組 4 - Streamlit 氣溫預報 Web App (40%)
    # -------------------------------------------------------------------------
    with col_left:
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <h3 style="margin:0; font-size:1.35rem; color:#0f172a;">
                <span style="background:#0284c7; color:white; padding:2px 8px; border-radius:6px; font-size:1rem; margin-right:6px;">4</span>
                Streamlit 氣溫預報 Web App (40%)
            </h3>
            <span style="font-size:0.8rem; color:#64748b;">範例：選擇地區顯示一週氣溫預報</span>
        </div>
        """, unsafe_allow_html=True)

        regions = database.get_distinct_regions()
        if not regions:
            st.warning("資料庫中尚無地區資料，請至側邊欄點選「載入 HW10 標準示範預報」。")
            st.stop()

        # 預設選中海報範例中的「中部地區」
        default_index = regions.index("中部地區") if "中部地區" in regions else 0
        selected_region = st.selectbox(
            "📍 選擇地區 (Select Region)：",
            regions,
            index=default_index,
            help="步驟 13：利用下拉選單選擇欲查詢的台灣分區"
        )

        region_df = database.get_forecasts_by_region(selected_region)

        if not region_df.empty:
            st.markdown(f"#### Temperature Forecast - {selected_region}")

            # 步驟 14：最高/最低溫折線圖 (精確對應海報 Card 4 設計)
            fig = go.Figure()

            # 最高溫 MaxT 紅線
            fig.add_trace(go.Scatter(
                x=region_df["dataDate"],
                y=region_df["maxT"],
                name="MaxT (最高溫)",
                mode="lines+markers+text",
                text=[f"{v}°" for v in region_df["maxT"]],
                textposition="top center",
                line=dict(color="#FF4136", width=3),
                marker=dict(size=9, color="#E53935", symbol="circle")
            ))

            # 最低溫 MinT 藍線
            fig.add_trace(go.Scatter(
                x=region_df["dataDate"],
                y=region_df["minT"],
                name="MinT (最低溫)",
                mode="lines+markers+text",
                text=[f"{v}°" for v in region_df["minT"]],
                textposition="bottom center",
                line=dict(color="#0074D9", width=3),
                marker=dict(size=9, color="#1E88E5", symbol="circle"),
                fill='tonexty',
                fillcolor='rgba(2, 132, 199, 0.08)'
            ))

            # 格式化日期標籤 (海報中為 04/14, 04/15 格式)
            date_labels = [d[5:] if len(d) >= 10 else d for d in region_df["dataDate"]]

            fig.update_layout(
                xaxis_title="Date (預報日期)",
                yaxis_title="Temperature (°C)",
                yaxis=dict(range=[10, 40], gridcolor="#e2e8f0"),
                xaxis=dict(
                    tickmode='array',
                    tickvals=region_df["dataDate"],
                    ticktext=date_labels,
                    gridcolor="#e2e8f0"
                ),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=15, r=15, t=35, b=20),
                height=310,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248, 250, 252, 0.7)"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 步驟 15：顯示一週資料表格 (對應海報 Card 4 右側表格)
            st.markdown(f"##### 📋 {selected_region} 一週氣象資料表格 (Table)")
            display_df = region_df[["dataDate", "minT", "maxT"]].copy()
            display_df.columns = ["Date", "MinT", "MaxT"]
            display_df["平均溫 (°C)"] = round((display_df["MinT"] + display_df["MaxT"]) / 2.0, 1)
            display_df["溫差 (°C)"] = round(display_df["MaxT"] - display_df["MinT"], 1)

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # 下載 CSV 按鈕
            csv_bytes = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"📥 下載 {selected_region} 一週氣溫預報 CSV",
                data=csv_bytes,
                file_name=f"{selected_region}_weather_7day.csv",
                mime="text/csv"
            )

    # -------------------------------------------------------------------------
    # 右欄：模組 5 - 進階：台灣地圖視覺化 (Optional) (Folium + Streamlit)
    # -------------------------------------------------------------------------
    with col_right:
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <h3 style="margin:0; font-size:1.35rem; color:#0f172a;">
                <span style="background:#0284c7; color:white; padding:2px 8px; border-radius:6px; font-size:1rem; margin-right:6px;">5</span>
                進階：台灣地圖視覺化 (Optional)
            </h3>
            <span style="font-size:0.8rem; color:#64748b;">Folium + Streamlit 互動地圖</span>
        </div>
        """, unsafe_allow_html=True)

        map_mode = st.radio(
            "地圖圖層模式：",
            ["📍 微課程六大分區 (海報標準)", "🌀 Windy 風場風格全台 340+ CWA 測站", "🍃 Edimax AirBox 物聯網"],
            index=0,
            horizontal=True
        )

        all_dates = database.get_distinct_dates()
        selected_date = all_dates[0] if all_dates else "2026-04-14"

        # 模式 1：微課程六大分區
        if map_mode == "📍 微課程六大分區 (海報標準)":
            if all_dates:
                selected_date = st.selectbox("📅 選擇預報日期 (Date)：", all_dates, index=0)

            # 模組 5 規範之四段溫度色階圖例
            st.markdown("""
            <div class="temp-legend-bar">
                <span>依平均溫度設定顏色：</span>
                <span><span class="legend-dot" style="background:#2196F3;"></span>&lt; 20°C (藍色)</span>
                <span><span class="legend-dot" style="background:#4CAF50;"></span>20 - 25°C (綠色)</span>
                <span><span class="legend-dot" style="background:#FFC107;"></span>25 - 30°C (黃色)</span>
                <span><span class="legend-dot" style="background:#F44336;"></span>&gt; 30°C (紅色)</span>
            </div>
            """, unsafe_allow_html=True)

            m = folium.Map(
                location=[23.75, 120.95],
                zoom_start=7.2,
                tiles="CartoDB positron"
            )

            date_df = database.get_forecasts_by_date(selected_date)
            for _, row in date_df.iterrows():
                r_name = row["regionName"]
                min_t = row["minT"]
                max_t = row["maxT"]
                avg_t = row["avgT"]
                coord = cwa_service.REGION_METADATA.get(r_name, {"lat": 23.97, "lon": 120.98})
                color_hex = get_temperature_color(avg_t)

                # Popup 彈出視窗 (完全符合海報 Card 5 右下角格式)
                popup_content = f"""
                <div style="font-family: sans-serif; font-size: 13px; width: 150px; line-height: 1.4;">
                    <div style="font-weight: bold; font-size: 15px; color: {color_hex}; margin-bottom: 4px;">{r_name}</div>
                    <div><b>Date:</b> {selected_date}</div>
                    <div><b>Min:</b> {min_t}°C</div>
                    <div><b>Max:</b> {max_t}°C</div>
                    <div style="margin-top: 4px; padding-top: 4px; border-top: 1px dashed #cbd5e1; color: #475569;">
                        平均溫：<b>{avg_t}°C</b>
                    </div>
                </div>
                """

                # 外圈色塊
                folium.CircleMarker(
                    location=[coord["lat"], coord["lon"]],
                    radius=22,
                    color=color_hex,
                    fill=True,
                    fill_color=color_hex,
                    fill_opacity=0.35,
                    tooltip=f"{r_name} (平均 {avg_t}°C)",
                    popup=folium.Popup(popup_content, max_width=200)
                ).add_to(m)

                # 中心實心小點
                folium.CircleMarker(
                    location=[coord["lat"], coord["lon"]],
                    radius=7,
                    color="#ffffff",
                    weight=2,
                    fill=True,
                    fill_color=color_hex,
                    fill_opacity=1.0,
                    popup=folium.Popup(popup_content, max_width=200)
                ).add_to(m)

            st_folium(m, width=540, height=440)

        # 模式 2：Windy 風格全台 340+ CWA 實體測站 (融入 Reference 參考設計)
        elif map_mode == "🌀 Windy 風場風格全台 340+ CWA 測站":
            st.caption("支援縣市篩選、溫度閾值、以及即時測站詳細數值彈窗 (Station, Humidity, Wind, Time)")
            
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                ok, _, _, stations = iot_service.fetch_taiwan_weather_map_data()
                all_counties = ["全部縣市"] + sorted(list({s["county"] for s in stations if s["county"]})) if ok else ["全部縣市"]
                selected_county = st.selectbox("篩選縣市 (County)：", all_counties, index=0)
            with c_col2:
                temp_filter = st.slider("最低氣溫過濾 (°C)：", 10.0, 35.0, 15.0, 1.0)

            # 溫度圖例
            st.markdown("""
            <div class="temp-legend-bar">
                <span>即時觀測色階：</span>
                <span><span class="legend-dot" style="background:#2b6cb0;"></span>&lt;15°C 涼爽</span>
                <span><span class="legend-dot" style="background:#38a169;"></span>15-25°C 舒適</span>
                <span><span class="legend-dot" style="background:#ed8936;"></span>25-30°C 溫暖</span>
                <span><span class="legend-dot" style="background:#e53e3e;"></span>&gt;30°C 炎熱</span>
            </div>
            """, unsafe_allow_html=True)

            m = folium.Map(location=[23.75, 120.95], zoom_start=7.3, tiles="CartoDB dark_matter")

            if ok and stations:
                # 篩選
                filtered_stations = [
                    s for s in stations 
                    if (selected_county == "全部縣市" or s["county"] == selected_county) 
                    and s["temperature"] >= temp_filter
                ]

                # 顯示前 250 個標記維持滑順
                for s in filtered_stations[:250]:
                    temp = s["temperature"]
                    c_hex = get_temperature_color(temp)

                    # Reference 彈窗結構：StationName, County, Town, Temp, Humidity, Wind, Time
                    obs_time = datetime.now().strftime("%Y-%m-%d %H:00")
                    popup_html = f"""
                    <div style="font-family:sans-serif; font-size:12px; width:160px; line-height:1.4;">
                        <b style="font-size:13px; color:{c_hex};">📍 {s['stationId']} {s['county']}{s['town']}</b><br>
                        氣溫 (Temp)：<b>{temp}°C</b><br>
                        濕度 (Humidity)：<b>{s['humidity']}%</b><br>
                        天氣 (Weather)：<b>{s['weather']}</b><br>
                        時間 (Observed)：{obs_time}
                    </div>
                    """
                    folium.CircleMarker(
                        location=[s["lat"], s["lon"]],
                        radius=5,
                        color=c_hex,
                        fill=True,
                        fill_color=c_hex,
                        fill_opacity=0.85,
                        tooltip=f"{s['county']}{s['town']}: {temp}°C",
                        popup=folium.Popup(popup_html, max_width=200)
                    ).add_to(m)

            st_folium(m, width=540, height=410)

        # 模式 3：Edimax AirBox 校園物聯網
        elif map_mode == "🍃 Edimax AirBox 物聯網":
            st.caption("全台校園 IoT 感測節點 (溫度 / 濕度 / PM2.5 空品)")
            air_df = database.get_all_airbox_readings(limit=100)
            if air_df.empty:
                ok, _, air_records = iot_service.fetch_airbox_edimax_data()
                if ok and air_records:
                    database.insert_airbox_readings(air_records)
                    air_df = database.get_all_airbox_readings(limit=100)

            m = folium.Map(location=[23.75, 120.95], zoom_start=7.3, tiles="CartoDB positron")
            for _, row in air_df.iterrows():
                pm_val = row["pm25"]
                c_pm = get_pm25_color(pm_val)
                pop_html = f"""
                <div style="font-family:sans-serif; font-size:12px; width:160px;">
                    <b style="color:#0284c7;">🍃 {row['siteName']}</b><br>
                    氣溫：<b>{row['temperature']}°C</b><br>
                    濕度：<b>{row['humidity']}%</b><br>
                    PM2.5：<b style="color:{c_pm};">{pm_val} μg/m³</b>
                </div>
                """
                folium.CircleMarker(
                    location=[row["lat"], row["lon"]],
                    radius=6,
                    color=c_pm,
                    fill=True,
                    fill_color=c_pm,
                    fill_opacity=0.8,
                    tooltip=f"{row['siteName']}: {row['temperature']}°C | PM2.5: {pm_val}",
                    popup=folium.Popup(pop_html, max_width=200)
                ).add_to(m)

            st_folium(m, width=540, height=440)


# =============================================================================
# 分頁 2：📋 HW10 課程專案架構全覽 (完全對應使用者所提供海報之 5 大卡片)
# =============================================================================
elif menu_choice == "📋 HW10 課程專案架構全覽 (Assignment Guide)":
    st.markdown("## 📋 HW10 Taiwan Weather Forecast 課程規格與五大模組全覽")
    st.caption("完整呈現 HW10 氣象資料到互動式天氣預報之作業規範、程式碼範例與評分指引")

    # 第一排：模組 1、2、3 (各佔 20%)
    c1, c2, c3 = st.columns(3)

    # 模組 1
    with c1:
        st.markdown("""
        <div class="module-card">
            <div class="module-header">
                <span class="module-badge">1</span>
                <span class="module-title">取得 CWA API 資料</span>
                <span class="module-score">(20%)</span>
            </div>
            <p><b>目標：</b>使用 CWA API 取得台灣六大區域一週天氣預報 (必須使用 JSON 格式)。</p>
            <div style="margin-bottom:8px;">
                <b>區域：</b><br>
                <span class="region-chip">北部地區</span>
                <span class="region-chip">中部地區</span>
                <span class="region-chip">南部地區</span><br>
                <span class="region-chip">東北部地區</span>
                <span class="region-chip">東部地區</span>
                <span class="region-chip">東南部地區</span>
            </div>
            <b>主要步驟：</b>
            <ol style="margin-top:4px; padding-left:18px; font-size:0.86rem; color:#334155;">
                <li>使用 requests 呼叫 CWA API</li>
                <li>使用 json.dumps 觀察回傳的 JSON 資料</li>
                <li>確認資料取得成功</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("💻 檢視 Module 1 核心程式碼", expanded=False):
            st.code("""
import requests, json

url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-A0010-001"
headers = {"Authorization": "YOUR_API_KEY"}
resp = requests.get(url, headers=headers, timeout=30)
data = resp.json()
print(json.dumps(data, indent=2, ensure_ascii=False))
            """, language="python")
            st.caption("評分項目：取得資料 10% ｜ 觀察JSON 5% ｜ 程式品質 5%")

    # 模組 2
    with c2:
        st.markdown("""
        <div class="module-card">
            <div class="module-header">
                <span class="module-badge">2</span>
                <span class="module-title">分析 JSON，提取氣溫資料</span>
                <span class="module-score">(20%)</span>
            </div>
            <p><b>目標：</b>分析 JSON 結構，找出並提取每日最高與最低氣溫。(Region 在資料中通常以 Location 表示)</p>
            <b>分析重點 (JSON 結構)：</b>
            <pre style="font-size:0.75rem; background:#f8fafc; padding:6px; border-radius:6px; border:1px solid #e2e8f0;">
JSON
└── records
    └── locations
        └── location[] (地區)
            └── weatherElement[] (天氣要素)
                └── time[] (預報日期)
                    ├── elementName: MinT (最低溫)
                    └── elementName: MaxT (最高溫)</pre>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📊 檢視 Module 2 提取結果範例", expanded=False):
            sample_table = pd.DataFrame([
                {"regionName": "北部地區", "dataDate": "2026-04-14", "mint": 18.0, "maxt": 26.0},
                {"regionName": "中部地區", "dataDate": "2026-04-14", "mint": 20.0, "maxt": 30.0},
                {"regionName": "南部地區", "dataDate": "2026-04-14", "mint": 22.0, "maxt": 31.0}
            ])
            st.dataframe(sample_table, use_container_width=True, hide_index=True)
            st.caption("評分項目：提取正確 10% ｜ 觀察資料 5% ｜ 程式品質 5%")

    # 模組 3
    with c3:
        st.markdown("""
        <div class="module-card">
            <div class="module-header">
                <span class="module-badge">3</span>
                <span class="module-title">存入 SQLite 資料庫</span>
                <span class="module-score">(20%)</span>
            </div>
            <p><b>目標：</b>將氣溫資料儲存到 SQLite 資料庫 (data.db)。</p>
            <b>資料庫設計：</b>
            <pre style="font-size:0.75rem; background:#f8fafc; padding:6px; border-radius:6px; border:1px solid #e2e8f0;">
CREATE TABLE TemperatureForecasts (
  id INTEGER PRIMARY KEY,
  regionName TEXT,
  dataDate TEXT,
  mint REAL,
  maxt REAL
);</pre>
            <b>驗證查詢：</b>
            <div style="font-size:0.82rem; color:#334155; margin-top:4px;">
                ① 列出所有地區名稱：<code>SELECT DISTINCT regionName...</code><br>
                ② 查詢中部地區資料：<code>SELECT * FROM ... WHERE regionName='中部地區';</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🔍 檢視 Module 3 評分與架構", expanded=False):
            st.caption("評分項目：儲存資料 10% ｜ 查詢驗證 5% ｜ 程式品質 5%")
            st.write("• 資料庫檔案：`data.db`")
            st.write("• 欄位：`id (PK)`, `regionName`, `dataDate`, `mint`, `maxt`")

    st.write("")

    # 第二排：模組 4 (40%) 與 模組 5 (進階加分)
    c4, c5 = st.columns([1.1, 0.9])

    with c4:
        st.markdown("""
        <div class="module-card">
            <div class="module-header">
                <span class="module-badge">4</span>
                <span class="module-title">Streamlit 氣溫預報 Web App</span>
                <span class="module-score">(40%)</span>
            </div>
            <p><b>目標：</b>建立互動式 Web App，從 SQLite 查詢資料，提供下拉選單，顯示一週氣溫的折線圖與表格。</p>
            <b>功能需求：</b>
            <ol style="margin-top:4px; padding-left:18px; font-size:0.88rem; color:#334155;">
                <li>下拉選單選擇地區 (北部、中部、南部、東北部、東部、東南部)</li>
                <li>使用 SQL 從 SQLite (data.db) 查詢資料</li>
                <li>顯示最高 (MaxT) / 最低溫 (MinT) 折線圖</li>
                <li>顯示一週 (7 天) 資料表格</li>
            </ol>
            <div style="font-size:0.85rem; color:#0284c7; font-weight:600; margin-top:8px;">
                評分項目：下拉選單 10% ｜ 折線圖與表格 15% ｜ SQLite 查詢 10% ｜ 程式品質 5%
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c5:
        st.markdown("""
        <div class="module-card">
            <div class="module-header">
                <span class="module-badge">5</span>
                <span class="module-title">進階：台灣地圖視覺化</span>
                <span class="module-score">(Optional 加分)</span>
            </div>
            <p><b>目標：</b>製作互動式台灣地圖，顯示各區當日平均溫度。(建議使用 Folium + Streamlit)</p>
            <b>依平均溫度設定顏色：</b>
            <div style="font-size:0.85rem; margin-top:6px; line-height:1.6;">
                🔵 <b>&lt; 20°C</b> (藍色)<br>
                🟢 <b>20 - 25°C</b> (綠色)<br>
                🟡 <b>25 - 30°C</b> (黃色)<br>
                🔴 <b>&gt; 30°C</b> (紅色)
            </div>
            <p style="font-size:0.82rem; color:#64748b; margin-top:6px;">
                包含 Marker 點擊跳出氣候詳細資訊 Popup (地區、Date、Min、Max)。
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 第三排：海報底部專案結構與執行說明
    st.markdown("### 🛠️ 專案結構、執行步驟與注意事項 (海報底部指南)")
    b1, b2, b3, b4 = st.columns(4)

    with b1:
        st.markdown("##### 📁 專案結構建議")
        st.code("""
HW10_weather/
├── fetch_weather.py
├── parse_weather.py
├── database.py
├── app.py
├── data.db
├── weather_data.csv
├── requirements.txt
└── README.md
        """, language="text")

    with b2:
        st.markdown("##### ⚙️ 執行方式 (4 步驟)")
        st.markdown("""
        1. **建立虛擬環境 (建議)**  
           `python -m venv venv`  
           `venv\\Scripts\\activate`
        2. **安裝套件**  
           `pip install -r requirements.txt`
        3. **執行資料處理 (一次即可)**  
           `python fetch_weather.py`  
           `python parse_weather.py`  
           `python database.py`
        4. **啟動 Web App**  
           `streamlit run app.py`
        """)

    with b3:
        st.markdown("##### 📦 需要安裝的套件")
        st.markdown("""
        - `requests`
        - `pandas`
        - `streamlit`
        - `folium`
        - `streamlit-folium`
        - `plotly`
        """)

    with b4:
        st.markdown("##### ⚠️ 重要注意事項")
        st.markdown("""
        1. 使用自己的 CWA API Key。
        2. **Streamlit 必須從 SQLite 查詢資料，不可直接呼叫 API**。
        3. 確保六個地區的資料都正確。
        4. 表格與圖表需顯示一週 (7天) 資料。
        5. 進階的台灣地圖為加分功能。
        """)

    st.info("💡 **用程式連結真實世界，讓資料說出天氣的故事！**")


# =============================================================================
# 分頁 3：🔍 SQLite 資料庫與 SQL 驗證 (Database Sandbox - 對應模組 3)
# =============================================================================
elif menu_choice == "🔍 SQLite 資料庫與 SQL 驗證 (Database Sandbox)":
    st.markdown("## 🔍 SQLite 資料庫檢查與 SQL 查詢驗證")
    st.caption("對應 HW10 模組 3：存入 SQLite 資料庫 (20%) 與驗證查詢")

    # 資料表結構預覽
    with st.expander("📐 檢視 data.db 與 TemperatureForecasts 資料表 Schema", expanded=True):
        st.code("""
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    mint REAL NOT NULL,
    maxt REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regionName, dataDate)
);
        """, language="sql")

    st.subheader("驗證查詢快捷按鈕 (HW10 海報標準語法)")
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        if st.button("① 執行驗證查詢 1：列出所有地區名稱", use_container_width=True):
            sql1 = "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName ASC;"
            res1 = database.execute_custom_sql(sql1)
            st.success("查詢 1 執行成功！")
            st.dataframe(res1, use_container_width=True)

    with q_col2:
        if st.button("② 執行驗證查詢 2：查詢中部地區資料", use_container_width=True):
            sql2 = "SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區' ORDER BY dataDate ASC;"
            res2 = database.execute_custom_sql(sql2)
            st.success("查詢 2 執行成功！")
            st.dataframe(res2, use_container_width=True)

    st.markdown("---")
    st.subheader("自由 SQL 執行沙盒")
    custom_sql = st.text_area(
        "輸入自訂 SQL 語法：",
        value="SELECT regionName, COUNT(*) as days, ROUND(AVG(minT),1) as avg_min, ROUND(AVG(maxT),1) as avg_max FROM TemperatureForecasts GROUP BY regionName;",
        height=85
    )

    if st.button("▶️ 執行自訂 SQL (Execute SQL)", type="primary"):
        try:
            custom_res = database.execute_custom_sql(custom_sql)
            st.success(f"查詢成功！共回傳 {len(custom_res)} 筆紀錄。")
            st.dataframe(custom_res, use_container_width=True)
        except Exception as e:
            st.error(f"SQL 語法錯誤：{str(e)}")


# =============================================================================
# 分頁 4：🔄 資料同步與 CWA API (Data Sync)
# =============================================================================
elif menu_choice == "🔄 資料同步與 CWA API (Data Sync)":
    st.markdown("## 🔄 資料同步與 CWA API 資料管線中心")
    st.caption("支援手動更新、載入海報基準示範數據，以及連線中央氣象署 API")

    tab_sync1, tab_sync2, tab_sync3 = st.tabs([
        "📄 載入 HW10 標準數據 (2026-04-14 ~ 2026-04-20)",
        "🏛️ 中央氣象署 (CWA) 官方 API / 自訂網址",
        "📡 全台即時氣象測站觀測同步"
    ])

    with tab_sync1:
        st.subheader("HW10 海報標準基準預報數據")
        st.write("此數據集包含中部地區、北部地區、南部地區、東北部地區、東部地區、東南部地區六大分區完整 7 天預報，數值完全精準對應 HW10 課程海報。")
        if st.button("🚀 立即重設並載入標準預報至 SQLite (data.db)", type="primary"):
            records = cwa_service.generate_sample_forecast_data("2026-04-14")
            cnt = database.insert_forecasts(records)
            st.success(f"✅ 成功將 {cnt} 筆六大分區預報存入 data.db！")
            st.dataframe(pd.DataFrame(records).head(12), use_container_width=True)

    with tab_sync2:
        st.subheader("呼叫 CWA API (F-A0010-001 或 F-D0047-091)")
        user_cwa_url = st.text_input("API 端點網址：", value=cwa_service.DEFAULT_CWA_API_URL)
        user_api_key = st.text_input("輸入個人 CWA API Key：", value="", type="password", help="注意事項 1：使用自己的 CWA API Key，不能使用老師提供的金鑰繳交。")

        if st.button("🚀 呼叫 API 並同步至 SQLite"):
            with st.spinner("正在連線至中央氣象署並解析 JSON..."):
                ok, msg, recs = cwa_service.fetch_weather_from_url(user_cwa_url, user_api_key)
                if ok and recs:
                    cnt, db_msg = cwa_service.sync_data_to_sqlite(recs)
                    st.success(f"✅ {db_msg}")
                    st.dataframe(pd.DataFrame(recs).head(10))
                else:
                    st.error(msg)

    with tab_sync3:
        st.subheader("全台 340+ 座自動氣象站即時資料")
        st.write("從中央氣象署觀測站彙整端點同步全台灣實體氣象站之即時氣溫與濕度。")
        if st.button("🚀 同步即時測站資料"):
            with st.spinner("正在安全連線同步中..."):
                ok, msg, reg_data, stn_data = iot_service.fetch_taiwan_weather_map_data(force_refresh=True)
                if ok:
                    count = database.insert_forecasts(reg_data)
                    st.success(f"✅ {msg}，已同步分區數值並更新即時觀測點！")
                else:
                    st.error(msg)
