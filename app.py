"""
app.py - Taiwan Weather Forecast 從氣象資料到互動式天氣預報 Web 應用程式
整合技術：
  - 微課程核心架構：CWA API × JSON × Python × SQLite × Streamlit
  - 即時資料源 1：台灣即時氣象地圖 (taiwan-weather-map.vercel.app)
  - 即時資料源 2：Edimax AirBox / LASS 台灣物聯網開放資料 (airbox.edimaxcloud.com)
  - 法律合規保障：OGDL-Taiwan 第一號、CC-BY-SA 開放授權、5分鐘防洪快取、透明署名
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import os
from datetime import datetime

# 匯入後端模組
import database
import cwa_service
import iot_service

# -----------------------------------------------------------------------------
# 頁面基本配置 (Streamlit Page Config)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Taiwan Weather & IoT Forecast | 台灣氣象與物聯網預報",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 全域 CSS 美化 (Modern UI, Glassmorphism, 圓角陰影與精緻字體)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 頂部主視覺 Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0d47a1 0%, #1565c0 40%, #00838f 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px rgba(13, 71, 161, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 900;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        opacity: 0.94;
        font-weight: 500;
    }
    .badge-chip {
        display: inline-block;
        background: rgba(255, 255, 255, 0.22);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        margin-right: 8px;
        margin-top: 8px;
        backdrop-filter: blur(4px);
    }

    /* 指標卡片 (Metric Cards) */
    .metric-container {
        background: #ffffff;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
        border: 1px solid #eef2f6;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1e293b;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-top: 2px;
    }

    /* 步驟 17 溫度色階圖例 */
    .legend-box {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 16px;
        margin-top: 10px;
        margin-bottom: 12px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .legend-color {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        margin-right: 6px;
    }

    /* 法律聲明橫幅 */
    .legal-badge {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        padding: 12px 18px;
        border-radius: 10px;
        font-size: 0.88rem;
        margin-bottom: 18px;
    }

    /* 卡片區塊 */
    .content-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        border: 1px solid #edf2f7;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 初始化資料庫
# -----------------------------------------------------------------------------
database.init_db()
existing_regions = database.get_distinct_regions()
if not existing_regions:
    # 預設載入示範一週預報
    sample_records = cwa_service.generate_sample_forecast_data()
    database.insert_forecasts(sample_records)


# -----------------------------------------------------------------------------
# 輔助函式：步驟 17 溫度色彩
# -----------------------------------------------------------------------------
def get_temperature_color(avg_temp: float) -> str:
    """步驟 17 規範：<20°C 藍色, 20-25°C 綠色, 25-30°C 橘黃色, >30°C 紅色"""
    if avg_temp < 20.0:
        return "#2196F3"
    elif avg_temp <= 25.0:
        return "#4CAF50"
    elif avg_temp <= 30.0:
        return "#FF9800"
    else:
        return "#F44336"


def get_pm25_color(pm25: float) -> str:
    """空氣品質 PM2.5 顏色標準 (綠/黃/橘/紅/紫)"""
    if pm25 <= 15.4:
        return "#4CAF50"  # 良好 綠
    elif pm25 <= 35.4:
        return "#FFEB3B"  # 普通 黃
    elif pm25 <= 54.4:
        return "#FF9800"  # 對敏感族群不健康 橘
    elif pm25 <= 150.4:
        return "#F44336"  # 對所有族群不健康 紅
    else:
        return "#9C27B0"  # 非常不健康 紫


# -----------------------------------------------------------------------------
# 側邊欄控制台 (Sidebar Controls)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/sun.png", width=85)
    st.title("氣象系統控制台")
    st.caption("碩士班 應用物聯網作業 | CWA × SQLite × Streamlit")
    st.markdown("---")

    menu_choice = st.radio(
        "選擇功能分頁：",
        [
            "🌤️ 天氣預報儀表板",
            "🌐 氣象與物聯網資料同步",
            "🔍 SQL 查詢與資料驗證",
            "⚖️ 開放資料授權與合法性說明",
            "📚 微課程 24 步學習導覽"
        ],
        index=0
    )

    st.markdown("---")
    st.subheader("⚡ 快速一鍵同步")

    # 快捷按鈕 1：同步台灣氣象地圖即時資料
    if st.button("📡 同步 台灣氣象地圖 資料", use_container_width=True, help="從 https://taiwan-weather-map.vercel.app 取得最新觀測站數據並存入 data.db"):
        with st.spinner("正在安全連線並同步台灣氣象地圖..."):
            ok, msg, reg_data, _ = iot_service.fetch_taiwan_weather_map_data(force_refresh=True)
            if ok and reg_data:
                database.insert_forecasts(reg_data)
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(msg)

    # 快捷按鈕 2：同步 Edimax AirBox 開放資料
    if st.button("🍃 同步 Edimax AirBox 資料", use_container_width=True, help="從 Edimax / LASS 開放資料端點同步全台校園 IoT 空氣盒子數據"):
        with st.spinner("正在安全連線並同步 AirBox 開放資料..."):
            ok, msg, air_records = iot_service.fetch_airbox_edimax_data(force_refresh=True)
            if ok and air_records:
                database.insert_airbox_readings(air_records)
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(msg)

    # 快捷按鈕 3：載入一週示範預報
    if st.button("🔄 載入微課程 7 天示範預報", use_container_width=True):
        samples = cwa_service.generate_sample_forecast_data()
        cwa_service.sync_data_to_sqlite(samples)
        st.success("✅ 已同步一週預報資料！")
        st.rerun()

    st.markdown("---")
    st.subheader("📊 資料庫即時統計")
    stats = database.get_summary_statistics()
    st.write(f"• **SQLite 檔案**：`data.db`")
    st.write(f"• **氣溫預報紀錄**：`{stats.get('total_records', 0)}` 筆")
    st.write(f"• **涵蓋分區數**：`{stats.get('total_regions', 0)}` 區")
    st.write(f"• **日期區間**：`{stats.get('start_date', 'N/A')}` ~ `{stats.get('end_date', 'N/A')}`")

    st.caption("🛡️ 具備 300 秒合規防洪快取，保障網站合法不超載。")


# -----------------------------------------------------------------------------
# 頂部主視覺橫幅 (Hero Banner)
# -----------------------------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🌤️ Taiwan Weather & IoT Forecast</div>
    <div class="hero-subtitle">從氣象資料到互動式天氣預報 ── 程式探索天氣 · 資料看見台灣 · 用 AI 實作</div>
    <div style="margin-top: 10px;">
        <span class="badge-chip">中央氣象署 CWA API</span>
        <span class="badge-chip">台灣即時氣象地圖</span>
        <span class="badge-chip">Edimax AirBox 開放物聯網</span>
        <span class="badge-chip">SQLite (data.db)</span>
        <span class="badge-chip">Streamlit Web App</span>
        <span class="badge-chip">Folium 地圖視覺化</span>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# 分頁 1：🌤️ 天氣預報儀表板 (Dashboard)
# =============================================================================
if menu_choice == "🌤️ 天氣預報儀表板":
    # 頂部 KPI 卡片
    stats = database.get_summary_statistics()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">全島預測平均溫</div>
            <div class="metric-value" style="color: #0288d1;">{stats.get('overall_avg_temp', 0)}°C</div>
            <div class="metric-sub">各地區綜合均溫</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">全島最高氣溫 (MaxT)</div>
            <div class="metric-value" style="color: #e53935;">{stats.get('highest_temp', 0)}°C</div>
            <div class="metric-sub">預報期間最高紀錄</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">全島最低氣溫 (MinT)</div>
            <div class="metric-value" style="color: #1e88e5;">{stats.get('lowest_temp', 0)}°C</div>
            <div class="metric-sub">預報期間最低紀錄</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        temp_range = round((stats.get('highest_temp', 0) - stats.get('lowest_temp', 0)), 1)
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">全島溫差幅度</div>
            <div class="metric-value" style="color: #f57c00;">{temp_range}°C</div>
            <div class="metric-sub">極值溫差範圍</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 雙欄佈局：左側折線圖與表格 (步驟 13-16)，右側 Folium 地圖 (步驟 17-19)
    left_col, right_col = st.columns([1.05, 0.95], gap="large")

    # -------------------------------------------------------------------------
    # 左側：步驟 13~16 整合 Web App 介面
    # -------------------------------------------------------------------------
    with left_col:
        st.subheader("📈 一週最高與最低氣溫走勢")
        st.caption("步驟 13 下拉選單選擇地區 ｜ 步驟 14 繪製折線圖 ｜ 步驟 15 顯示資料表格")

        regions = database.get_distinct_regions()
        if not regions:
            st.warning("資料庫中尚無資料，請從左側點選「載入微課程 7 天示範預報」。")
            st.stop()

        default_idx = regions.index("中部地區") if "中部地區" in regions else 0
        selected_region = st.selectbox(
            "📍 選擇地區 (Select Region)：",
            regions,
            index=default_idx
        )

        region_df = database.get_forecasts_by_region(selected_region)

        if not region_df.empty:
            # 步驟 14：折線圖
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=region_df["dataDate"],
                y=region_df["maxT"],
                name="最高氣溫 (MaxT)",
                mode="lines+markers+text",
                text=[f"{v}°" for v in region_df["maxT"]],
                textposition="top center",
                line=dict(color="#FF5722", width=3),
                marker=dict(size=8, color="#D84315")
            ))
            fig.add_trace(go.Scatter(
                x=region_df["dataDate"],
                y=region_df["minT"],
                name="最低氣溫 (MinT)",
                mode="lines+markers+text",
                text=[f"{v}°" for v in region_df["minT"]],
                textposition="bottom center",
                line=dict(color="#1976D2", width=3),
                marker=dict(size=8, color="#0D47A1"),
                fill='tonexty',
                fillcolor='rgba(33, 150, 243, 0.08)'
            ))
            fig.update_layout(
                title=f"{selected_region} 氣溫走勢 (°C)",
                xaxis_title="預報日期 (Date)",
                yaxis_title="氣溫 (°C)",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=15, r=15, t=45, b=20),
                height=330,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(248, 250, 252, 0.8)",
                yaxis=dict(gridcolor="#e2e8f0"),
                xaxis=dict(gridcolor="#e2e8f0")
            )
            st.plotly_chart(fig, use_container_width=True)

            # 步驟 15：顯示資料表格
            st.markdown("##### 📋 資料庫即時紀錄表格")
            display_df = region_df[["dataDate", "minT", "maxT", "avgT"]].copy()
            display_df["tempDiff"] = round(display_df["maxT"] - display_df["minT"], 1)
            display_df.columns = ["日期 (dataDate)", "最低溫 (°C)", "最高溫 (°C)", "平均溫 (°C)", "溫差 (°C)"]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"📥 下載 {selected_region} 氣溫預報 CSV",
                data=csv_data,
                file_name=f"{selected_region}_weather_forecast.csv",
                mime="text/csv"
            )

    # -------------------------------------------------------------------------
    # 右側：步驟 17~19 台灣地圖視覺化 (Folium + Streamlit + AirBox IoT)
    # -------------------------------------------------------------------------
    with right_col:
        st.subheader("🗺️ 台灣地圖互動視覺化")
        st.caption("步驟 17 台灣地圖視覺化 ｜ 步驟 18 選擇日期顯示地圖 ｜ 整合 AirBox 物聯網")

        # 圖層篩選控制
        map_layer_mode = st.radio(
            "地圖展示圖層：",
            ["📍 微課程五大分區 (預設)", "📡 台灣氣象地圖 340+ 即時觀測站", "🍃 Edimax AirBox 台灣校園物聯網節點"],
            index=0,
            horizontal=True
        )

        all_dates = database.get_distinct_dates()
        selected_date = all_dates[0] if all_dates else datetime.now().strftime("%Y-%m-%d")
        if all_dates and map_layer_mode == "📍 微課程五大分區 (預設)":
            selected_date = st.selectbox("📅 選擇預報日期 (Select Date)：", all_dates, index=0)

        # 步驟 17 溫度色階圖例
        st.markdown("""
        <div class="legend-box">
            <span style="font-weight: 700; color: #475569; margin-right: 6px;">平均溫度色階：</span>
            <div class="legend-item"><div class="legend-color" style="background:#2196F3;"></div>&lt; 20°C (藍)</div>
            <div class="legend-item"><div class="legend-color" style="background:#4CAF50;"></div>20 - 25°C (綠)</div>
            <div class="legend-item"><div class="legend-color" style="background:#FF9800;"></div>25 - 30°C (黃)</div>
            <div class="legend-item"><div class="legend-color" style="background:#F44336;"></div>&gt; 30°C (紅)</div>
        </div>
        """, unsafe_allow_html=True)

        # 建立 Folium 地圖
        m = folium.Map(
            location=[23.8, 120.95],
            zoom_start=7.2,
            tiles="CartoDB positron"
        )

        # 圖層 1：微課程五大分區
        if map_layer_mode == "📍 微課程五大分區 (預設)":
            date_df = database.get_forecasts_by_date(selected_date)
            for _, row in date_df.iterrows():
                r_name = row["regionName"]
                min_t = row["minT"]
                max_t = row["maxT"]
                avg_t = row["avgT"]
                coord = cwa_service.REGION_METADATA.get(r_name, {"lat": 23.97, "lon": 120.98, "desc": "台灣氣象分區"})
                color_hex = get_temperature_color(avg_t)

                popup_html = f"""
                <div style="font-family: sans-serif; font-size: 13px; width: 170px;">
                    <h4 style="margin: 0 0 6px 0; color: {color_hex}; font-weight: bold;">📍 {r_name}</h4>
                    <div style="color: #64748b; font-size: 11px;">預報日期：{selected_date}</div>
                    <div style="background: #f1f5f9; padding: 6px; border-radius: 6px; margin: 6px 0;">
                        <div>🌡️ 最低溫: {min_t}°C</div>
                        <div>🔥 最高溫: {max_t}°C</div>
                        <div>📊 平均溫: <b>{avg_t}°C</b></div>
                    </div>
                </div>
                """
                folium.CircleMarker(
                    location=[coord["lat"], coord["lon"]],
                    radius=24,
                    color=color_hex,
                    fill=True,
                    fill_color=color_hex,
                    fill_opacity=0.35,
                    tooltip=f"{r_name} (平均 {avg_t}°C)",
                    popup=folium.Popup(popup_html, max_width=240)
                ).add_to(m)

                folium.CircleMarker(
                    location=[coord["lat"], coord["lon"]],
                    radius=6,
                    color="#ffffff",
                    weight=2,
                    fill=True,
                    fill_color=color_hex,
                    fill_opacity=1.0
                ).add_to(m)

        # 圖層 2：台灣氣象地圖 340+ 即時測站
        elif map_layer_mode == "📡 台灣氣象地圖 340+ 即時觀測站":
            ok, _, _, stations = iot_service.fetch_taiwan_weather_map_data()
            if ok and stations:
                for stn in stations[:200]:  # 渲染前 200 個測站維持順暢流暢度
                    temp = stn["temperature"]
                    c_hex = get_temperature_color(temp)
                    pop_html = f"""
                    <div style="font-family: sans-serif; font-size: 12px; width: 150px;">
                        <b>{stn['county']} {stn['town']} 站</b><br>
                        站號: {stn['stationId']}<br>
                        氣溫: <b style="color:{c_hex}">{temp}°C</b><br>
                        濕度: {stn['humidity']}%<br>
                        天氣: {stn['weather']}
                    </div>
                    """
                    folium.CircleMarker(
                        location=[stn["lat"], stn["lon"]],
                        radius=5,
                        color=c_hex,
                        fill=True,
                        fill_color=c_hex,
                        fill_opacity=0.85,
                        tooltip=f"{stn['county']}{stn['town']}: {temp}°C ({stn['weather']})",
                        popup=folium.Popup(pop_html, max_width=200)
                    ).add_to(m)

        # 圖層 3：Edimax AirBox 台灣校園物聯網節點
        elif map_layer_mode == "🍃 Edimax AirBox 台灣校園物聯網節點":
            air_df = database.get_all_airbox_readings(limit=120)
            if air_df.empty:
                ok, _, air_records = iot_service.fetch_airbox_edimax_data()
                if ok and air_records:
                    database.insert_airbox_readings(air_records)
                    air_df = database.get_all_airbox_readings(limit=120)

            for _, row in air_df.iterrows():
                pm_val = row["pm25"]
                t_val = row["temperature"]
                h_val = row["humidity"]
                c_pm = get_pm25_color(pm_val)

                pop_html = f"""
                <div style="font-family: sans-serif; font-size: 12px; width: 170px;">
                    <div style="color: #0284c7; font-weight: bold;">🍃 {row['siteName']}</div>
                    <div style="color: #64748b; font-size: 10px;">時間: {row['observedTime']}</div>
                    <div style="margin-top: 4px; padding: 4px 6px; background: #f8fafc; border-radius: 4px;">
                        <div>🌡️ 氣溫: <b>{t_val}°C</b></div>
                        <div>💧 濕度: <b>{h_val}%</b></div>
                        <div>💨 PM2.5: <b style="color:{c_pm}">{pm_val} μg/m³</b></div>
                    </div>
                </div>
                """
                folium.CircleMarker(
                    location=[row["lat"], row["lon"]],
                    radius=7,
                    color=c_pm,
                    fill=True,
                    fill_color=c_pm,
                    fill_opacity=0.75,
                    tooltip=f"{row['siteName']}: {t_val}°C / PM2.5: {pm_val}",
                    popup=folium.Popup(pop_html, max_width=220)
                ).add_to(m)

        st_folium(m, width=540, height=420)


# =============================================================================
# 分頁 2：🌐 氣象與物聯網資料同步
# =============================================================================
elif menu_choice == "🌐 氣象與物聯網資料同步":
    st.header("🌐 即時氣象與物聯網資料同步中心")
    st.markdown("""
    <div class="legal-badge">
        🛡️ <b>合法授權防護聲明</b>：本系統嚴格遵循開放資料授權條款 (OGDL-Taiwan & LASS CC-BY-SA)。所有遠端資料請求均配置 <b>300 秒智慧快取</b> 與 <b>學術專屬 User-Agent</b>，防範高頻輪詢與爬蟲違法風險，保障您的系統 100% 合法、健康運作。
    </div>
    """, unsafe_allow_html=True)

    tab_src1, tab_src2, tab_src3 = st.tabs([
        "📡 台灣即時氣象地圖 (taiwan-weather-map)",
        "🍃 Edimax AirBox 開放資料 (airbox.edimaxcloud.com)",
        "🏛️ 中央氣象署 CWA API / 自訂網址"
    ])

    with tab_src1:
        st.subheader("來源 1: 台灣即時氣象地圖 (taiwan-weather-map.vercel.app)")
        st.write("來源特性：彙整中央氣象署 CWA O-A0003-001 開放資料，提供全台 340+ 座自動氣象站的高頻觀測值。")
        if st.button("🚀 立即連線同步並存入 SQLite", type="primary", key="sync_tw_map"):
            with st.spinner("正在進行合規請求與 JSON 結構解析..."):
                ok, msg, reg_data, stn_data = iot_service.fetch_taiwan_weather_map_data(force_refresh=True)
                if ok:
                    count = database.insert_forecasts(reg_data)
                    st.success(f"{msg}，並已將 {count} 筆分區紀錄寫入 TemperatureForecasts 資料表！")
                    st.json(reg_data[:3])
                else:
                    st.error(msg)

    with tab_src2:
        st.subheader("來源 2: Edimax AirBox / LASS 台灣物聯網開放資料 (airbox.edimaxcloud.com)")
        st.write("來源特性：由中研院資訊所 (IIS-NRL) 與訊舟科技 (Edimax) 共同營運之台灣環境感測開放資料網，涵蓋全台各級校園 IoT 節點。")
        if st.button("🚀 立即連線同步 AirBox 物聯網資料", type="primary", key="sync_airbox"):
            with st.spinner("正在安全擷取 AirBox 物聯網節點數據..."):
                ok, msg, air_records = iot_service.fetch_airbox_edimax_data(force_refresh=True)
                if ok:
                    cnt = database.insert_airbox_readings(air_records)
                    st.success(f"{msg}，已更新至 AirBoxReadings 資料表！")
                    st.dataframe(pd.DataFrame(air_records).head(5))
                else:
                    st.error(msg)

    with tab_src3:
        st.subheader("來源 3: 中央氣象署 CWA 官方開放資料 / 自訂網址")
        custom_url = st.text_input("輸入自訂 API 網址：", value=cwa_service.DEFAULT_CWA_API_URL)
        custom_key = st.text_input("API Key (授權碼，選填)：", value="", type="password")
        if st.button("🚀 請求自訂網址並解析存入 SQLite", key="sync_cwa"):
            with st.spinner("正在請求目標伺服器..."):
                ok, msg, records = cwa_service.fetch_weather_from_url(custom_url, custom_key)
                if ok:
                    count, db_msg = cwa_service.sync_data_to_sqlite(records)
                    st.success(db_msg)
                else:
                    st.error(msg)


# =============================================================================
# 分頁 3：🔍 SQL 查詢與資料驗證 (步驟 10 & 12)
# =============================================================================
elif menu_choice == "🔍 SQL 查詢與資料驗證":
    st.header("🔍 SQLite 資料庫檢查與 SQL 查詢驗證")
    st.caption("對應步驟 8、9、10、12：資料庫設計、SQL 查詢驗證、Pandas 資料讀取")

    with st.expander("📐 查看 TemperatureForecasts 與 AirBoxReadings 資料表結構", expanded=False):
        st.code("""
-- 1. 微課程標準氣溫預報資料表
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate TEXT NOT NULL,
    minT REAL NOT NULL,
    maxT REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regionName, dataDate)
);

-- 2. Edimax AirBox 台灣物聯網感測資料表
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
        """, language="sql")

    st.subheader("步驟 10：常用 SQL 查詢範本")
    preset_query = st.selectbox(
        "選擇微課程範例 SQL 語法：",
        [
            "SELECT DISTINCT regionName FROM TemperatureForecasts;",
            "SELECT * FROM TemperatureForecasts WHERE regionName = '中部地區' ORDER BY dataDate;",
            "SELECT regionName, ROUND(AVG(minT), 1) AS avg_min, ROUND(AVG(maxT), 1) AS avg_max FROM TemperatureForecasts GROUP BY regionName;",
            "SELECT siteName, temperature, humidity, pm25 FROM AirBoxReadings LIMIT 15;"
        ]
    )

    custom_sql = st.text_area("SQL 執行編輯區：", value=preset_query, height=90)

    if st.button("▶️ 執行 SQL 查詢 (Execute SQL)", type="primary"):
        try:
            sql_result = database.execute_custom_sql(custom_sql)
            st.success(f"查詢成功！共回傳 {len(sql_result)} 筆資料。")
            st.dataframe(sql_result, use_container_width=True)
        except Exception as e:
            st.error(f"SQL 執行發生錯誤：{str(e)}")


# =============================================================================
# 分頁 4：⚖️ 開放資料授權與合法性說明 (DO NOT LET MY WEBSITE BECOME ILLEGAL)
# =============================================================================
elif menu_choice == "⚖️ 開放資料授權與合法性說明":
    st.header("⚖️ 資料來源合法性與安全防護機制")
    st.markdown("""
    為確保本網站完全符合台灣與國際網路法規，杜絕「未授權爬蟲」、「分散式阻斷服務 (DDoS)」或「侵犯智慧財產權」之疑慮，本系統實施以下合規架構：
    """)

    st.markdown("""
    ### 1. 資料授權條款依據
    - **中央氣象署氣象資料**：依據中華民國「**政府資料開放授權條款 (Open Government Data License, OGDL-Taiwan) 第一號**」，開放所有學術、個人與商業利用，條件為依規定標示來源。
    - **Edimax AirBox / LASS 物聯網開放資料**：訊舟科技與中央研究院資訊科技創新研究中心 (IIS-NRL) 合作推動之社群開放資料，採用「**創用 CC 姓名標示-相同方式分享 (CC-BY-SA 4.0)**」授權，鼓勵物聯網研究與教學使用。

    ### 2. 技術防護措施 (杜絕違法爬蟲與防洪)
    1. **智慧記憶體快取 (Smart In-Memory Caching)**：系統預設 300 秒 (5 分鐘) 的 TTL 快取機制，使用者反覆重新整理或點擊地圖時，不會頻繁向原始伺服器發送網路請求，保護遠端伺服器頻寬。
    2. **學術專屬 User-Agent 標頭 (Transparent Identity)**：所有 HTTP 請求均帶有合法身分聲明：
       `User-Agent: Taiwan-IoT-Academic-Course-Project/1.0 (Master Degree IoT Coursework)`，公開透明，絕無偽裝或惡意刺探。
    3. **無個資與會員資料處理**：本系統僅讀取公開大氣物理數值 (氣溫、濕度、PM2.5、風速)，完全不涉及任何個人隱私、帳號密碼或機敏資訊。
    4. **SQLite 本地持久化**：資料落地至 `data.db`，離線亦可正常運作展示，符合物聯網邊緣運算 (Edge Computing) 標準設計。
    """)


# =============================================================================
# 分頁 5：📚 微課程 24 步學習導覽
# =============================================================================
elif menu_choice == "📚 微課程 24 步學習導覽":
    st.header("📚 AI 創新微課程：Taiwan Weather Forecast 完整 24 步驟學習地圖")
    steps_data = [
        {"num": "1", "title": "課程介紹", "desc": "AI × 資料 × 天氣 × 實作，學習地圖與專案成果展示。"},
        {"num": "2", "title": "台灣的天氣與生活", "desc": "氣象的重要性、資料驅動決策、智慧物聯網應用。"},
        {"num": "3", "title": "中央氣象署 CWA Open Data", "desc": "註冊平台帳號、取得授權 API Key、選擇目標氣象資料集。"},
        {"num": "4", "title": "API 資料取得", "desc": "使用 Python Requests 函式庫發送 GET 請求取得 JSON。"},
        {"num": "5", "title": "JSON 資料結構解析", "desc": "解析 locations、weatherElement 等巢狀階層物件。"},
        {"num": "6", "title": "提取最高與最低氣溫", "desc": "提取 MinT 與 MaxT 資料並進行結構化轉換。"},
        {"num": "7", "title": "資料整理與預覽", "desc": "使用 Pandas DataFrame 組織表格並預覽資料分佈。"},
        {"num": "8", "title": "建立 SQLite 資料庫", "desc": "建立 data.db 資料庫檔案，定義關聯式資料結構。"},
        {"num": "9", "title": "資料庫設計", "desc": "建立 TemperatureForecasts 資料表 (regionName, dataDate, minT, maxT)。"},
        {"num": "10", "title": "查詢資料驗證", "desc": "使用 SQL 檢查資料完整性與欄位內容。"},
        {"num": "11", "title": "Streamlit 入門", "desc": "快速建立互動式 Web 應用程式與版面設定。"},
        {"num": "12", "title": "從資料庫讀取資料", "desc": "使用 pd.read_sql_query 從 SQLite 撈取即時氣象資料。"},
        {"num": "13", "title": "下拉選單選擇地區", "desc": "利用 st.selectbox 實現使用者互動式地區篩選。"},
        {"num": "14", "title": "繪製折線圖", "desc": "呈現一週最高溫 (MaxT) 與最低溫 (MinT) 的趨勢走勢圖。"},
        {"num": "15", "title": "顯示資料表格", "desc": "以結構化表格清晰展示一週詳細氣象溫度數值。"},
        {"num": "16", "title": "整合 Web App 介面", "desc": "串接選單、圖表、表格與指標卡片，完成一體化 UI。"},
        {"num": "17", "title": "進階：台灣地圖視覺化", "desc": "利用 Folium 地圖標註各區，依四段溫度色階顯示高低溫。"},
        {"num": "18", "title": "選擇日期顯示地圖", "desc": "互動式切換日期，點擊地圖標記跳出詳細氣象數值。"},
        {"num": "19", "title": "完整成果展示", "desc": "Taiwan Weather Dashboard 專業級綜合展示。"},
        {"num": "20", "title": "程式碼品質與優化", "desc": "模組化設計、異常捕捉、重複執行不重複插入 (UPSERT)。"},
        {"num": "21", "title": "專案上傳至 GitHub", "desc": "版本控制 Git、.gitignore 與 README 撰寫。"},
        {"num": "22", "title": "延伸應用與想法", "desc": "天氣通知 Bot、旅遊建議、智慧物聯網防災預警。"},
        {"num": "23", "title": "回顧與重點整理", "desc": "盤點 API、JSON、SQLite、Streamlit 全端技能。"},
        {"num": "24", "title": "下一步：繼續探索", "desc": "串接更多 IoT 感測資料與邊緣裝置，實現智慧物聯網。"}
    ]

    for i in range(0, len(steps_data), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(steps_data):
                item = steps_data[i + j]
                with cols[j]:
                    st.markdown(f"""
                    <div class="content-card" style="min-height: 160px;">
                        <span style="background: #e0f2fe; color: #0284c7; padding: 2px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">步驟 {item['num']}</span>
                        <h4 style="margin: 8px 0 4px 0; font-size: 1.02rem;">{item['title']}</h4>
                        <p style="font-size: 0.83rem; color: #64748b; margin: 0;">{item['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True)
