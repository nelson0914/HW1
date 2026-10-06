"""
app.py - Taiwan Weather Forecast 從氣象資料到互動式天氣預報應用程式
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
    page_title="Taiwan Weather Forecast | 互動式天氣預報應用程式",
    page_icon="⛅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 全域 CSS 美化 (現代科技主題、精緻卡片、圓角陰影與字體)
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

    /* 頂部主視覺 Banner */
    .weather-hero-banner {
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
    .weather-hero-banner::after {
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

    /* 流程架構指示條 (Architecture Flow Bar) */
    .weather-flow-container {
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
# 資料庫初始化與即時氣象資料就緒檢查 (100% 即時更新)
# -----------------------------------------------------------------------------
@st.cache_resource
def _init_database():
    """初始化資料庫並自動進行即時氣象連線同步"""
    database.init_db()
    try:
        iot_service.sync_all_realtime_weather(force_refresh=False)
    except Exception:
        today_s = datetime.now().strftime("%Y-%m-%d")
        sample_records = cwa_service.generate_sample_forecast_data(today_s)
        database.insert_forecasts(sample_records)
    return True

_init_database()


# -----------------------------------------------------------------------------
# 輔助函式：溫度色階與 AirBox 色彩標準
# -----------------------------------------------------------------------------
def get_temperature_color(avg_temp: float) -> str:
    """
    溫度色階規範：
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
    """空氣品質 PM2.5 顏色標準 (對應 AirBox / 環保署指標)"""
    if pm25 <= 15.4:
        return "#10b981"  # 綠色 (良好)
    elif pm25 <= 35.4:
        return "#eab308"  # 黃色 (普通)
    elif pm25 <= 54.4:
        return "#f97316"  # 橘色 (對敏感族群不健康)
    elif pm25 <= 150.4:
        return "#ef4444"  # 紅色 (對所有族群不健康)
    else:
        return "#a855f7"  # 紫色 (非常不健康/危害)


def get_humidity_color(humidity: float) -> str:
    """相對濕度顏色標準"""
    if humidity > 80:
        return "#1d4ed8"  # 深藍 (潮濕)
    elif humidity >= 65:
        return "#0284c7"  # 淺藍 (適濕)
    elif humidity >= 50:
        return "#10b981"  # 綠色 (舒適)
    else:
        return "#f59e0b"  # 橙色 (乾燥)


# -----------------------------------------------------------------------------
# 側邊欄控制台 (Sidebar Controls)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/sun.png", width=75)
    st.title("氣象預報控制台")
    st.caption("CWA API × JSON × SQLite × Streamlit")
    st.markdown("---")

    menu_choice = st.radio(
        "選擇功能分頁：",
        [
            "🌤️ 氣溫預報 Web App (Live Dashboard)",
            "🔍 SQLite 資料庫與 SQL 驗證 (Database Sandbox)",
            "🔄 資料同步與 CWA API (Data Sync)"
        ],
        index=0
    )

    st.markdown("---")
    st.subheader("⚡ 即時資料操作")

    if st.button("🔄 立即重新整理所有天氣 (Live Sync)", use_container_width=True, type="primary"):
        with st.spinner("正在連線更新全台 340+ 氣象測站與 AirBox 物聯網節點..."):
            sync_res = iot_service.sync_all_realtime_weather(force_refresh=True)
            if sync_res.get("success"):
                st.success(f"✅ {sync_res.get('message')}")
                st.rerun()
            else:
                st.error("同步失敗，請檢查網路連線。")

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
# 頂部主視覺橫幅 (Hero Banner)
# -----------------------------------------------------------------------------
st.markdown("""
<div class="weather-hero-banner">
    <div class="banner-top-row">
        <div class="banner-title-left">
            <span style="font-size: 2.8rem;">🌤️</span>
            <div>
                <div class="banner-title-text">Taiwan Weather Forecast</div>
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
# 系統架構流程與學習重點條 (Architecture Flow Bar)
# -----------------------------------------------------------------------------
st.markdown("""
<div class="weather-flow-container">
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
            st.warning("資料庫中尚無地區資料，請至側邊欄點選「立即重新整理所有天氣 (Live Sync)」。")
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
    # 右欄：模組 5 - 進階：全球衛星雲圖與全台即時物聯網 (AirBox Style · 100% 即時更新)
    # -------------------------------------------------------------------------
    with col_right:
        st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <h3 style="margin:0; font-size:1.3rem; color:#0f172a;">
                <span style="background:#0284c7; color:white; padding:2px 8px; border-radius:6px; font-size:0.95rem; margin-right:6px;">5</span>
                進階：全球衛星雲圖與即時物聯網 (AirBox Style)
            </h3>
            <span style="font-size:0.75rem; background:#dcfce7; color:#15803d; padding:2px 8px; border-radius:12px; font-weight:700;">
                🟢 100% 即時更新
            </span>
        </div>
        """, unsafe_allow_html=True)

        # 取得全台即時資料
        sync_res = iot_service.sync_all_realtime_weather(force_refresh=False)
        cwa_stations = sync_res.get("cwa_stations", [])
        airbox_stations = sync_res.get("airbox_stations", [])
        radar_url = sync_res.get("radar_tile_url")
        last_updated = sync_res.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # 即時數據快報與重新整理按鈕
        st_row1, st_row2 = st.columns([2.8, 1.2])
        with st_row1:
            st.markdown(f"""
            <div style="font-size:0.78rem; color:#334155; line-height:1.45; padding:6px 10px; background:#f1f5f9; border-radius:8px; border-left:4px solid #0284c7; margin-bottom:8px;">
                📡 <b>即時測站總數</b>：<b>{len(cwa_stations) + len(airbox_stations)}</b> 站 (氣象署 {len(cwa_stations)} + AirBox {len(airbox_stations)})<br>
                🌡️ <b>全台均溫</b>：<b>{sync_res.get('avg_temp', 25.0)}°C</b> ｜ 🍃 <b>平均 PM2.5</b>：<b>{sync_res.get('avg_pm25', 15.0)} μg/m³</b> ｜ 🕒 <b>{last_updated}</b>
            </div>
            """, unsafe_allow_html=True)
        with st_row2:
            if st.button("🔄 刷新即時數據", use_container_width=True, type="primary"):
                iot_service.sync_all_realtime_weather(force_refresh=True)
                st.rerun()

        # 地圖控制列
        ctl_c1, ctl_c2 = st.columns(2)
        with ctl_c1:
            map_base = st.selectbox(
                "🗺️ 地圖底圖樣式 (Map Style)：",
                [
                    "🛰️ 全球衛星雲圖 (Esri World Imagery)",
                    "🌌 AirBox 經典深色夜空圖 (CartoDB Dark)",
                    "🗺️ 簡潔高對比街道圖 (CartoDB Positron)"
                ],
                index=0
            )
        with ctl_c2:
            metric_mode = st.selectbox(
                "📊 觀測指標 (Metric)：",
                [
                    "🌡️ 即時氣溫 (°C)",
                    "🍃 空氣品質 PM2.5 (μg/m³)",
                    "💧 相對濕度 (%)"
                ],
                index=0
            )

        ctl_c3, ctl_c4 = st.columns(2)
        with ctl_c3:
            all_counties = ["全部縣市"] + sorted(list({s.get("county") for s in cwa_stations if s.get("county")}))
            selected_county = st.selectbox("📍 篩選縣市 (County)：", all_counties, index=0)
        with ctl_c4:
            station_layer = st.selectbox(
                "📡 測站圖層篩選 (Layer)：",
                [
                    "🌐 全部站點 (CWA + AirBox + 六大分區)",
                    "🏛️ 中央氣象署 (CWA) 實體站",
                    "🍃 Edimax AirBox 物聯網節點",
                    "📍 六大分區核心看板"
                ],
                index=0
            )

        radar_overlay = st.checkbox("☁️ 疊加 RainViewer 全球即時雷達衛星雲圖 (Radar Clouds)", value=True)

        # 動態圖例列
        if "氣溫" in metric_mode:
            st.markdown("""
            <div class="temp-legend-bar" style="margin-bottom:8px;">
                <span>氣溫色階：</span>
                <span><span class="legend-dot" style="background:#2196F3;"></span>&lt; 20°C 涼爽</span>
                <span><span class="legend-dot" style="background:#4CAF50;"></span>20-25°C 舒適</span>
                <span><span class="legend-dot" style="background:#FFC107;"></span>25-30°C 溫暖</span>
                <span><span class="legend-dot" style="background:#F44336;"></span>&gt; 30°C 炎熱</span>
            </div>
            """, unsafe_allow_html=True)
        elif "PM2.5" in metric_mode:
            st.markdown("""
            <div class="temp-legend-bar" style="margin-bottom:8px;">
                <span>PM2.5 空品：</span>
                <span><span class="legend-dot" style="background:#10b981;"></span>≤15.4 良好</span>
                <span><span class="legend-dot" style="background:#eab308;"></span>≤35.4 普通</span>
                <span><span class="legend-dot" style="background:#f97316;"></span>≤54.4 敏感族群</span>
                <span><span class="legend-dot" style="background:#ef4444;"></span>≤150.4 不健康</span>
                <span><span class="legend-dot" style="background:#a855f7;"></span>&gt;150.4 危害</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="temp-legend-bar" style="margin-bottom:8px;">
                <span>相對濕度：</span>
                <span><span class="legend-dot" style="background:#f59e0b;"></span>&lt;50% 乾燥</span>
                <span><span class="legend-dot" style="background:#10b981;"></span>50-65% 舒適</span>
                <span><span class="legend-dot" style="background:#0284c7;"></span>65-80% 適濕</span>
                <span><span class="legend-dot" style="background:#1d4ed8;"></span>&gt;80% 潮濕</span>
            </div>
            """, unsafe_allow_html=True)

        # 構建 Folium 地圖
        m = folium.Map(
            location=[23.75, 120.95],
            zoom_start=7.3,
            tiles=None
        )

        # 底圖
        if "衛星" in map_base:
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri World Imagery",
                name="🛰️ 全球衛星空照圖",
                overlay=False,
                control=False
            ).add_to(m)
        elif "深色" in map_base:
            folium.TileLayer(tiles="CartoDB dark_matter", name="CartoDB Dark", overlay=False, control=False).add_to(m)
        else:
            folium.TileLayer(tiles="CartoDB positron", name="CartoDB Positron", overlay=False, control=False).add_to(m)

        # 即時雷達衛星雲圖疊加層
        if radar_overlay and radar_url:
            folium.TileLayer(
                tiles=radar_url,
                attr="RainViewer Radar & Clouds",
                name="即時雷達衛星雲圖",
                opacity=0.62,
                overlay=True
            ).add_to(m)

        # 1. 繪製六大分區核心看板
        if "全部" in station_layer or "六大分區" in station_layer:
            today_date_str = datetime.now().strftime("%Y-%m-%d")
            reg_df = database.get_forecasts_by_date(today_date_str)
            for _, r_row in reg_df.iterrows():
                r_name = r_row["regionName"]
                coord = cwa_service.REGION_METADATA.get(r_name, {"lat": 23.97, "lon": 120.98})
                r_min = r_row["minT"]
                r_max = r_row["maxT"]
                r_avg = r_row["avgT"]
                r_color = get_temperature_color(r_avg)

                pop_reg = f"""
                <div style="font-family:'Noto Sans TC',sans-serif; background:#0f172a; color:#f8fafc; padding:10px 12px; border-radius:8px; width:180px; line-height:1.45; box-shadow:0 8px 24px rgba(0,0,0,0.5);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-size:10px; background:#0284c7; color:#fff; padding:2px 6px; border-radius:4px; font-weight:700;">六大分區看板</span>
                        <span style="font-size:10px; color:#94a3b8;">{today_date_str}</span>
                    </div>
                    <b style="font-size:14px; color:{r_color};">📍 {r_name}</b><br>
                    <hr style="border:0; border-top:1px solid #334155; margin:5px 0;">
                    <div style="font-size:12px; line-height:1.6;">
                        <div>本日最低溫：<b style="color:#60a5fa;">{r_min}°C</b></div>
                        <div>本日最高溫：<b style="color:#f87171;">{r_max}°C</b></div>
                        <div>本日平均溫：<b style="color:#fde047;">{r_avg}°C</b></div>
                    </div>
                    <div style="margin-top:6px; font-size:10px; color:#94a3b8; border-top:1px dashed #334155; padding-top:4px;">
                        {coord.get('desc', '')}
                    </div>
                </div>
                """

                # 外層脈衝光暈
                folium.CircleMarker(
                    location=[coord["lat"], coord["lon"]],
                    radius=20,
                    color=r_color,
                    weight=2,
                    fill=True,
                    fill_color=r_color,
                    fill_opacity=0.35,
                    tooltip=f"📍 {r_name}：平均 {r_avg}°C (即時)",
                    popup=folium.Popup(pop_reg, max_width=220)
                ).add_to(m)

                # 中心醒目標記
                folium.CircleMarker(
                    location=[coord["lat"], coord["lon"]],
                    radius=7,
                    color="#ffffff",
                    weight=2,
                    fill=True,
                    fill_color=r_color,
                    fill_opacity=1.0,
                    popup=folium.Popup(pop_reg, max_width=220)
                ).add_to(m)

        # 2. 繪製 CWA 實體測站 (348+ 站)
        if ("全部" in station_layer or "中央氣象署" in station_layer) and cwa_stations:
            filtered_cwa = [
                s for s in cwa_stations
                if (selected_county == "全部縣市" or s.get("county") == selected_county)
            ]
            for s in filtered_cwa[:200]:
                temp = s.get("temperature", 25.0)
                hum = s.get("humidity", 70.0)
                weather_desc = s.get("weather", "多雲")

                if "氣溫" in metric_mode:
                    c_hex = get_temperature_color(temp)
                    metric_label = f"氣溫: {temp}°C"
                elif "PM2.5" in metric_mode:
                    c_hex = get_pm25_color(15.0)
                    metric_label = f"氣溫: {temp}°C (CWA站)"
                else:
                    c_hex = get_humidity_color(hum)
                    metric_label = f"濕度: {hum}%"

                pop_cwa = f"""
                <div style="font-family:'Noto Sans TC',sans-serif; background:#0f172a; color:#f8fafc; padding:10px 12px; border-radius:8px; width:180px; line-height:1.45; box-shadow:0 8px 24px rgba(0,0,0,0.5);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-size:10px; background:#0284c7; color:#fff; padding:2px 6px; border-radius:4px; font-weight:700;">🏛️ CWA 實體測站</span>
                        <span style="font-size:10px; color:#94a3b8;">即時觀測</span>
                    </div>
                    <b style="font-size:13px; color:#38bdf8;">📍 {s.get('stationId')} {s.get('county')}{s.get('town')}</b>
                    <hr style="border:0; border-top:1px solid #334155; margin:5px 0;">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; font-size:11px;">
                        <div>🌡️ 氣溫: <b style="color:{get_temperature_color(temp)}; font-size:12px;">{temp}°C</b></div>
                        <div>💧 濕度: <b>{hum}%</b></div>
                        <div style="grid-column:span 2;">🌤️ 天氣狀態: <b>{weather_desc}</b></div>
                        <div style="grid-column:span 2; font-size:10px; color:#94a3b8;">觀測時間: {last_updated}</div>
                    </div>
                </div>
                """

                folium.CircleMarker(
                    location=[s["lat"], s["lon"]],
                    radius=5,
                    color=c_hex,
                    weight=1.5,
                    fill=True,
                    fill_color=c_hex,
                    fill_opacity=0.85,
                    tooltip=f"{s.get('county')}{s.get('town')}: {metric_label}",
                    popup=folium.Popup(pop_cwa, max_width=210)
                ).add_to(m)

        # 3. 繪製 Edimax AirBox 物聯網節點 (150+ 站)
        if ("全部" in station_layer or "AirBox" in station_layer) and airbox_stations:
            filtered_air = [
                a for a in airbox_stations
                if (selected_county == "全部縣市" or selected_county in a.get("area", "") or selected_county in a.get("siteName", ""))
            ]
            for a in filtered_air[:150]:
                temp = a.get("temperature", 25.0)
                hum = a.get("humidity", 70.0)
                pm25 = a.get("pm25", 15.0)
                site = a.get("siteName", "AirBox 節點")

                if "氣溫" in metric_mode:
                    c_hex = get_temperature_color(temp)
                    metric_label = f"{temp}°C"
                elif "PM2.5" in metric_mode:
                    c_hex = get_pm25_color(pm25)
                    metric_label = f"PM2.5: {pm25}"
                else:
                    c_hex = get_humidity_color(hum)
                    metric_label = f"濕度: {hum}%"

                pop_air = f"""
                <div style="font-family:'Noto Sans TC',sans-serif; background:#0f172a; color:#f8fafc; padding:10px 12px; border-radius:8px; width:180px; line-height:1.45; box-shadow:0 8px 24px rgba(0,0,0,0.5);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-size:10px; background:#10b981; color:#fff; padding:2px 6px; border-radius:4px; font-weight:700;">🍃 Edimax AirBox</span>
                        <span style="font-size:10px; color:#94a3b8;">IoT 即時</span>
                    </div>
                    <b style="font-size:13px; color:#a7f3d0;">🏫 {site}</b>
                    <hr style="border:0; border-top:1px solid #334155; margin:5px 0;">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px; font-size:11px;">
                        <div>🌡️ 氣溫: <b>{temp}°C</b></div>
                        <div>💧 濕度: <b>{hum}%</b></div>
                        <div style="grid-column:span 2;">🍃 PM2.5: <b style="color:{get_pm25_color(pm25)}; font-size:12px;">{pm25} μg/m³</b></div>
                        <div style="grid-column:span 2; font-size:10px; color:#94a3b8;">觀測時間: {a.get('observedTime', last_updated)}</div>
                    </div>
                </div>
                """

                # AirBox 經典發光雙層標記
                folium.CircleMarker(
                    location=[a["lat"], a["lon"]],
                    radius=6,
                    color=c_hex,
                    weight=1,
                    fill=True,
                    fill_color=c_hex,
                    fill_opacity=0.45,
                    tooltip=f"{site}: {metric_label}",
                    popup=folium.Popup(pop_air, max_width=210)
                ).add_to(m)

                folium.CircleMarker(
                    location=[a["lat"], a["lon"]],
                    radius=3,
                    color="#ffffff",
                    weight=1,
                    fill=True,
                    fill_color=c_hex,
                    fill_opacity=1.0,
                    popup=folium.Popup(pop_air, max_width=210)
                ).add_to(m)

        st_folium(m, width=540, height=440)


# =============================================================================
# 分頁 2：🔍 SQLite 資料庫與 SQL 驗證 (Database Sandbox)
# =============================================================================
elif menu_choice == "🔍 SQLite 資料庫與 SQL 驗證 (Database Sandbox)":
    st.markdown("## 🔍 SQLite 資料庫檢查與 SQL 查詢驗證")
    st.caption("SQLite 資料庫檢查與 SQL 查詢驗證")

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

    st.subheader("驗證查詢快捷按鈕 (標準 SQL 語法)")
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
# 分頁 3：🔄 資料同步與 CWA API (Data Sync)
# =============================================================================
elif menu_choice == "🔄 資料同步與 CWA API (Data Sync)":
    st.markdown("## 🔄 資料同步與 CWA API 資料管線中心")
    st.caption("支援手動更新、載入基準示範數據，以及連線中央氣象署 API")

    tab_sync1, tab_sync2, tab_sync3 = st.tabs([
        "📄 載入標準基準預報數據",
        "🏛️ 中央氣象署 (CWA) 官方 API / 自訂網址",
        "📡 全台即時氣象測站觀測同步"
    ])

    with tab_sync1:
        st.subheader("標準基準預報數據")
        st.write("此數據集包含中部地區、北部地區、南部地區、東北部地區、東部地區、東南部地區六大分區完整 7 天預報。")
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
