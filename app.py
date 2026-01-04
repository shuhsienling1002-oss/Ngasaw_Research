import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import math
import random

# --- 0. 系統設定與 CSS 風格注入 ---
st.set_page_config(
    page_title="Amis Navigator: 尋根版",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入自定義 CSS (溫暖、明亮、文化感)
st.markdown("""
<style>
    /* 全局背景 - 柔和米白 */
    .stApp { background-color: #fffbf0; color: #2c3e50; }
    
    /* 標題風格 - 大地色系 */
    h1, h2, h3 {
        font-family: 'Noto Sans TC', sans-serif;
        color: #8b4513 !important; /* SaddleBrown */
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* 資訊卡片 - 像紙張一樣的質感 */
    .clan-card {
        background-color: #ffffff;
        border: 1px solid #e0d4c3;
        border-left: 5px solid #d2691e; /* Chocolate */
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .clan-card:hover {
        transform: translateY(-3px);
        border-color: #d2691e;
    }
    
    /* ID 卡 - 儀式感 */
    .id-card-container {
        background: linear-gradient(135deg, #fff 0%, #fdf5e6 100%);
        border: 2px solid #cd853f; /* Peru */
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(139, 69, 19, 0.1);
        font-family: monospace;
        color: #5d4037;
    }
    
    /* 側邊欄引言區塊 */
    .wisdom-box {
        background-color: #f0e6d2;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #8b4513;
        font-style: italic;
        color: #5d4037;
        margin-bottom: 20px;
    }

    /* 按鈕樣式優化 */
    div.stButton > button {
        background-color: #fff;
        border: 1px solid #8b4513;
        color: #8b4513;
    }
    div.stButton > button:hover {
        background-color: #8b4513;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- [尋根數據] ---

CANGKANG_COORDS = [23.398, 121.488]

# 預設資料庫 (Data Updated: Foladan/Kakopa/Monari' Locations Corrected)
DEFAULT_CLAN_DB = [
    {"id": "pacidal", "name": "Pacidal", "meaning": "太陽", "algo": "高地優勢 / 監控者", "origin": "花蓮月眉 / 豐富", "lat": 23.931, "lon": 121.535, "icon": "☀️", "color": "#d97706"},
    {"id": "ciwidian", "name": "Ciwidian", "meaning": "水蛭", "algo": "水源豐沛 / 濕地農業", "origin": "花蓮水璉村", "lat": 23.778, "lon": 121.564, "icon": "💧", "color": "#2563eb"},
    {"id": "sadipongan", "name": "Sadipongan", "meaning": "鳥巢", "algo": "物理屏障 / 安全庇護", "origin": "石梯坪", "lat": 23.488, "lon": 121.503, "icon": "🛡️", "color": "#4b5563"},
    {"id": "cikatopay", "name": "Cikatopay", "meaning": "大葉山欖", "algo": "濱海防風林 / 沿海資源", "origin": "大港口", "lat": 23.498, "lon": 121.501, "icon": "🌳", "color": "#16a34a"},
    {"id": "cilangasan", "name": "Cilangasan", "meaning": "聖山", "algo": "制高點 / 正統根源", "origin": "八里灣山頂", "lat": 23.545, "lon": 121.489, "icon": "⛰️", "color": "#9333ea"},
    # [FIXED] Foladan -> 豐濱鄉的靜埔 (Jingpu)
    {"id": "foladan", "name": "Foladan", "meaning": "月亮", "algo": "縱谷平原 / 曆法對應", "origin": "豐濱鄉的靜埔", "lat": 23.460, "lon": 121.500, "icon": "🌙", "color": "#4f46e5"},
    # [FIXED] Kakopa -> 綠島 (Green Island)
    {"id": "kakopa", "name": "Kakopa", "meaning": "牛車", "algo": "戰術運輸 / 後勤載重", "origin": "綠島", "lat": 22.665, "lon": 121.495, "icon": "🐂", "color": "#ea580c"},
    # [FIXED] Monari' -> 大港口 (Dagangkou)
    {"id": "monari", "name": "Monari'", "meaning": "茅草", "algo": "在地資材庫 / 建材控制", "origin": "大港口", "lat": 23.498, "lon": 121.501, "icon": "⛺", "color": "#b45309"}
]

# 尋根小語 (隨機顯示)
ROOTS_QUOTES = [
    "「不要忘記你的名字，那是祖先回家的路。」",
    "「土地不會說話，但它記得我們每一個人的腳步。」",
    "「像大葉山欖一樣扎根，像太陽一樣照耀部落。」",
    "「海浪帶我們去遠方，但洋流終會帶我們回家。」",
    "「氏族是我們的根，部落是我們的家。」",
    "「聽，風裡有耆老的歌聲。」",
    "「我們都是 Cilangasan 聖山的孩子。」"
]

# 初始化 Session State
if 'clan_data' not in st.session_state:
    st.session_state.clan_data = DEFAULT_CLAN_DB

df_clans = pd.DataFrame(st.session_state.clan_data)

# --- 運算邏輯 ---

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_temporal_buffer(dist_km, speed_kmh=4.0):
    base_time = dist_km / speed_kmh
    buffer = base_time * 0.2
    min_time = base_time - buffer
    max_time = base_time + buffer
    return base_time, min_time, max_time

def check_physical_accessibility():
    # 尋根版降低一點阻礙機率，讓學生體驗更順暢
    status = random.choices(["暢通", "受阻"], weights=[0.9, 0.1])[0]
    return status

# --- 2. 介面層 (UI Layout) ---

with st.sidebar:
    st.title("🌱 氏族導航")
    st.caption("Amis Navigator: 尋根之旅")
    st.divider()
    
    # 祖靈的指引
    st.markdown("### 🏔️ 祖靈的指引")
    
    # 隨機選取一句尋根小語
    quote = random.choice(ROOTS_QUOTES)
    
    st.markdown(f"""
    <div class="wisdom-box">
        {quote}
    </div>
    """, unsafe_allow_html=True)
    
    st.info("當你迷失方向時，記得抬頭看看聖山，或者低頭問問土地。")
    
    st.divider()
    
    # 重置按鈕
    if st.button("🔄 重新啟動旅程 (Reset)"):
        st.session_state.clan_data = DEFAULT_CLAN_DB
        st.rerun()
    st.caption("若地圖資料混亂，可點此回到起點。")

# 主標題
st.title("Pangcah 氏族尋根終端")
st.markdown("連結過去與未來的數位路徑 // 學生協作系統")

# 分頁選單
tab1, tab2, tab3, tab4 = st.tabs(["📜 氏族傳說 (Database)", "👣 尋根地圖 (Map)", "🪪 認同協議 (ID Card)", "➕ 延續傳承 (Add Node)"])

# --- Tab 1: 數據庫 ---
with tab1:
    st.subheader("氏族記憶與特徵")
    cols = st.columns(2)
    for idx, clan in df_clans.iterrows():
        col_idx = idx % 2
        with cols[col_idx]:
            st.markdown(f"""
            <div class="clan-card">
                <div style="font-size: 1.5rem; color: {clan['color']}; display: flex; justify-content: space-between; align-items: center;">
                    <b>{clan['name']}</b>
                    <span style="font-size: 2rem;">{clan['icon']}</span>
                </div>
                <div style="color: #8b4513; font-family: monospace; font-size: 0.9rem; margin-top: 5px; font-weight: bold;">
                    象徵 (Meaning): {clan['meaning']}
                </div>
                <div style="background: #fdf5e6; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 0.9rem; color: #5d4037;">
                    <b>🧬 生存智慧 (Algo):</b><br>{clan['algo']}
                </div>
                <div style="margin-top: 8px; font-size: 0.85rem; color: #8d6e63; font-family: monospace;">
                    📍 發源地 (ORIGIN): {clan['origin']}
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- Tab 2: 尋根地圖 ---
with tab2:
    st.subheader("重返發源地")
    
    col_map_ctrl, col_map_view = st.columns([1, 2])
    
    with col_map_ctrl:
        st.markdown("#### 🎯 選擇你的氏族")
        selected_clan_name = st.selectbox(
            "選擇目標氏族 (Select Target)",
            df_clans['name'].tolist()
        )
        
        target_clan = df_clans[df_clans['name'] == selected_clan_name].iloc[0]
        
        dist = calculate_distance(CANGKANG_COORDS[0], CANGKANG_COORDS[1], target_clan['lat'], target_clan['lon'])
        base_t, min_t, max_t = calculate_temporal_buffer(dist)
        road_status = check_physical_accessibility()
        
        st.divider()
        st.markdown(f"**GPS 座標:** `{target_clan['lat']}, {target_clan['lon']}`")
        st.metric("直線距離 (Distance)", f"{dist:.2f} km")
        
        if road_status == "受阻":
            st.warning("⚠️ 路途艱辛 (Path Blocked): \n古道目前難以通行，但心意可以抵達。")
            line_color = "#d9534f" # 柔和紅
            line_dash = "5, 10"
        else:
            st.success("✅ 路徑暢通 (Path Clear)")
            st.markdown(f"**徒步尋根預估時間:**")
            st.info(f"約 **{base_t:.1f} 小時** (含休息與緩衝)")
            line_color = "#d2691e" # 大地色線條
            line_dash = "10"
            
            gmap_url = f"https://www.google.com/maps/dir/?api=1&origin={CANGKANG_COORDS[0]},{CANGKANG_COORDS[1]}&destination={target_clan['lat']},{target_clan['lon']}&travelmode=walking"
            st.link_button("🚀 開啟 Google Maps 導航", gmap_url)

    with col_map_view:
        # 使用地形圖層，更有尋根感
        m = folium.Map(tiles='CartoDB positron') 
        
        folium.Marker(
            CANGKANG_COORDS,
            popup="長光部落 (出發地)",
            icon=folium.Icon(color="green", icon="home")
        ).add_to(m)
        
        folium.Marker(
            [target_clan['lat'], target_clan['lon']],
            popup=f"{target_clan['name']}",
            icon=folium.Icon(color="orange", icon="star", prefix='fa')
        ).add_to(m)
        
        folium.PolyLine(
            locations=[CANGKANG_COORDS, [target_clan['lat'], target_clan['lon']]],
            color=line_color,
            weight=4,
            opacity=0.8,
            dash_array=line_dash,
            tooltip=f"路況: {road_status}"
        ).add_to(m)
        
        m.fit_bounds([CANGKANG_COORDS, [target_clan['lat'], target_clan['lon']]])
        st_folium(m, width="100%", height=500)

# --- Tab 3: 身分協議 ---
with tab3:
    st.subheader("建立自我認同")
    
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        st.markdown("#### 📝 寫下你的名字")
        input_name = st.text_input("你的名字 (UNIT ID / 自然名)", placeholder="例如: Panay")
        input_mother = st.text_input("媽媽的名字 (LINKAGE NODE)", placeholder="例如: Moli")
        input_clan_obj = st.selectbox("你的氏族 (ORIGIN CODE)", df_clans['name'].tolist(), key="id_clan_select")
        id_clan_data = df_clans[df_clans['name'] == input_clan_obj].iloc[0]
        
    with col_preview:
        disp_name = input_name if input_name else "UNKNOWN"
        disp_mother = input_mother if input_mother else "N/A"
        
        st.markdown(f"""
        <div class="id-card-container">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #deb887; padding-bottom: 10px; margin-bottom: 15px;">
                <span style="color: #8b4513; font-weight: bold; letter-spacing: 1px; font-size: 1.1rem;">AMIS IDENTITY LOG</span>
                <span style="font-size: 0.8rem; color: #a1887f;">尋根紀錄 V6.1</span>
            </div>
            <div style="display: flex; gap: 20px;">
                <div style="width: 100px; height: 100px; border: 2px dashed #cd853f; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 8px; background: rgba(205, 133, 63, 0.1);">
                    <div style="font-size: 3rem;">{id_clan_data['icon']}</div>
                    <div style="font-size: 0.6rem; color: #8b4513; margin-top: 5px; font-weight: bold;">圖騰 (TOTEM)</div>
                </div>
                <div style="flex: 1;">
                    <div style="margin-bottom: 10px;">
                        <div style="font-size: 0.75rem; color: #8d6e63; font-weight: bold;">名字 (UNIT ID)</div>
                        <div style="font-size: 1.8rem; font-weight: bold; color: #3e2723; line-height: 1.2;">{disp_name}</div>
                        <div style="font-size: 0.9rem; color: #d2691e;">母親 (Linkage): {disp_mother}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #8d6e63; font-weight: bold;">源頭 / 氏族 (CLAN)</div>
                        <span style="background-color: #fff8e1; color: #8b4513; padding: 4px 10px; border-radius: 4px; font-size: 0.9rem; font-weight: bold; border: 1px solid #ffe082;">
                            {id_clan_data['id'].upper()}
                        </span>
                    </div>
                </div>
            </div>
            <div style="margin-top: 15px; padding-top: 10px; border-top: 2px solid #deb887; display: flex; justify-content: space-between; align-items: flex-end;">
                <div style="font-size: 0.75rem; color: #8d6e63;">發源地定位: <span style="color: #2e7d32; font-weight: bold;">{id_clan_data['lat']}, {id_clan_data['lon']}</span></div>
                <div style="color: #2e7d32; font-size: 1.2rem;">📶</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        csv_data = pd.DataFrame([{
            "UNIT_ID": disp_name,
            "LINKAGE": disp_mother,
            "CLAN": id_clan_data['name'],
            "COORDS": f"{id_clan_data['lat']}, {id_clan_data['lon']}",
            "TIMESTAMP": pd.Timestamp.now().isoformat()
        }])
        csv = csv_data.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="💾 下載紀錄卡 (.CSV)",
            data=csv,
            file_name=f"AMIS_ID_{disp_name}.csv",
            mime="text/csv",
        )

# --- Tab 4: 延續傳承 ---
with tab4:
    st.subheader("延續傳承 (Protocol Extension)")
    st.markdown("當你發現了新的故事，請將它記錄下來，讓地圖變得更完整。")
    
    with st.form("add_clan_form"):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            new_name = st.text_input("氏族名稱 (Name / 羅馬拼音)", placeholder="例如: Raranges") 
            new_meaning = st.text_input("象徵意義 (Meaning)", placeholder="例如: 石柱")
            new_origin = st.text_input("發源地 (Origin)", placeholder="例如: 瑞穗溫泉")
            new_icon = st.text_input("代表圖示 (Icon / Emoji)", value="📍")
        
        with col_f2:
            new_algo = st.text_area("生存智慧 (Survival Wisdom)", placeholder="描述這個氏族是怎麼生活的？靠海？靠山？還是擅長種植？")
            st.markdown("**物理坐標 (GPS Coordinates)**")
            new_lat = st.number_input("緯度 (Latitude)", value=23.400, format="%.4f")
            new_lon = st.number_input("經度 (Longitude)", value=121.400, format="%.4f")
            new_color = st.color_picker("標記顏色 (Marker Color)", "#8b4513")
        
        submitted = st.form_submit_button("💾 記錄這個氏族 (Save Node)")
        
        if submitted:
            if new_name and new_meaning:
                new_entry = {
                    "id": new_name.split()[0].lower(),
                    "name": new_name,
                    "meaning": new_meaning,
                    "algo": new_algo if new_algo else "未記錄 (Undefined)",
                    "origin": new_origin,
                    "lat": new_lat,
                    "lon": new_lon,
                    "icon": new_icon,
                    "color": new_color
                }
                
                st.session_state.clan_data.append(new_entry)
                st.success(f"[{new_name}] 的故事已加入地圖中！")
                st.rerun()
            else:
                st.error("請填寫氏族名稱與象徵意義。")

st.divider()
st.markdown("<div style='text-align: center; color: #8d6e63; font-size: 0.8rem;'>Pangcah 氏族尋根系統 | 連結過去，邁向未來</div>", unsafe_allow_html=True)
