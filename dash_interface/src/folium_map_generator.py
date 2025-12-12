# src/folium_map_generator.py (Final Folium Version - 最终修复)

import folium 
import pandas as pd 
import os 
import numpy as np 
import branca.colormap as cm 
from dash import html
# 导入所有需要的常量
from src.data_loader import DF_DATA, FARE_COL, ROUTE_COL, PASSENGER_COL 

# ----------------------------------------------------------------------
# 路径常量：请确保您的项目根目录下有 'assets' 文件夹
# ----------------------------------------------------------------------
MAP_HTML_PATH = os.path.join(os.getcwd(), 'assets', 'folium_map.html')

# Core Constants (保持不变)
AIRPORT_COORDS = {
    "LAX": (33.9416, -118.4090), "LAS": (36.0800, -115.1522),
    "DEN": (39.8500, -104.6740), "JFK": (40.6413, -73.7781),
    "ORD": (41.9742, -87.9073), "DFW": (32.8998, -97.0403),
    "SFO": (37.6213, -122.3790), "SEA": (47.4502, -122.3088),
    "MCO": (28.4312, -81.3080),
}

OD_PAIRS = [
    ("LAX", "LAS"), ("DEN", "JFK"), ("ORD", "DFW"), 
    ("LAX", "SFO"), ("JFK", "MCO"), ("SFO", "SEA"),
]

# --- 辅助函数：计算并绘制单个 KPI 图层 ---
def _add_kpi_layer(m, kpi_name, kpi_col, agg_func, is_fare):
    """Calculates KPI stats and adds a FeatureGroup layer to the map."""
    
    # [DEBUG] 1. 记录开始
    print(f"\n--- 正在处理 KPI 图层: {kpi_name} (列: {kpi_col}) ---")
    
    # 1. 聚合计算
    route_stats = DF_DATA.groupby(['Origin', 'Dest'])[kpi_col].agg(agg_func).reset_index()
    route_stats['Route'] = route_stats['Origin'] + '-' + route_stats['Dest']
    route_stats.rename(columns={kpi_col: 'KPI_Value'}, inplace=True)
    
    # [DEBUG] 2. 检查聚合结果
    print(f"数据聚合后包含 {len(route_stats)} 条潜在路线统计。")
    
    # 2. 过滤核心航线数据并计算 min/max
    required_routes = [f"{o}-{d}" for o, d in OD_PAIRS]
    kpi_values = route_stats[route_stats['Route'].isin(required_routes)]['KPI_Value'].dropna()
    
    if kpi_values.empty:
        status_msg = f"⚠️ 无效数据: {kpi_name} 图层没有有效的 KPI 值，请检查数据过滤结果。"
        print(f"[DEBUG ❌] {status_msg}") 
        return None, None, status_msg
        
    min_val = kpi_values.min()
    max_val = kpi_values.max()
    
    # [DEBUG] 4. 打印 min/max 值
    print(f"[DEBUG ✅] 过滤后的核心路线 KPI 值范围: Min={min_val:.2f}, Max={max_val:.2f}")

    # 3. 健壮性检查：确保 min/max 差异大于零
    if min_val == max_val:
        max_val = min_val + 1 
        print(f"[DEBUG ⚠️] Min/Max 值相等，已将 Max 调整为 {max_val:.2f} 以防止除零错误。")
        
    # 4. 创建 FeatureGroup 图层 (票价默认显示)
    fg = folium.FeatureGroup(name=kpi_name, show=is_fare) 
    caption = "Average Market Fare ($)" if is_fare else "Total Passenger Volume"
    
    # 5. 创建颜色图例 (Branca Colormap)
    # RdYlGn_04 顺序: Red (低) -> Yellow (中) -> Green (高)
    if is_fare:
        # FARE (票价): 低票价 (min_val) 是好的 (绿色), 高票价 (max_val) 是差的 (红色)
        colormap = cm.linear.RdYlGn_04.scale(max_val, min_val) 
        unit = '$'
    else:
        # VOLUME (客运量): 低客运量 (min_val) 是差的 (红色), 高客运量 (max_val) 是好的 (绿色)
        colormap = cm.linear.RdYlGn_04.scale(min_val, max_val)
        unit = ''
        
    colormap.caption = caption 
    # 📢 关键修改：将 colormap 从 fg 中移除，改为在 create_folium_map 中添加到 m
    # fg.add_child(colormap) 
    
    # 6. 绘制路线
    min_weight, max_weight = 2, 8 
    range_diff = max_val - min_val
    if range_diff == 0: range_diff = 1 # 确保除数不为零
            
    num_routes_drawn = 0
    for origin, dest in OD_PAIRS:
        route_str = f"{origin}-{dest}"
        route_data = route_stats.query("Origin == @origin and Dest == @dest")
        
        if not route_data.empty:
            kpi_value = route_data['KPI_Value'].iloc[0]
            
            if pd.isna(kpi_value): 
                print(f"[DEBUG ⚠️] 路线 {route_str} KPI 值为 NaN，跳过绘制。")
                continue 
                 
            line_color = colormap(kpi_value)
            
            # 归一化计算 (控制线条粗细)
            normalized_kpi = (kpi_value - min_val) / range_diff
            line_weight = min_weight + normalized_kpi * (max_weight - min_weight)
            
            tooltip_val = f"{kpi_value:.2f}" if is_fare else f"{kpi_value:,.0f}"
            tooltip_text = f"Route: {route_str}<br>{caption}: {unit}{tooltip_val}"
            
            folium.PolyLine(
                [AIRPORT_COORDS[origin], AIRPORT_COORDS[dest]],
                color=line_color,
                weight=line_weight,
                opacity=0.8,
                tooltip=tooltip_text
            ).add_to(fg)
            
            num_routes_drawn += 1
            
    fg.add_to(m)
    status_msg = f"✅ 成功生成 {num_routes_drawn} 条路线。"
    print(f"[DEBUG ✅] {kpi_name} 图层绘制完毕。绘制了 {num_routes_drawn} 条路线。") 
    return fg, colormap, status_msg

# --- 核心函数：创建交互式地图 ---
def create_folium_map():
    
    print("\n========================================================")
    print("🚀 正在启动 create_folium_map 函数...")
    print(f"数据帧 DF_DATA 状态: {'为空' if DF_DATA.empty else f'包含 {len(DF_DATA)} 行数据'}")
    print("========================================================")
    
    # 1. 初始化 folium map
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4, tiles="CartoDB positron")
    folium.TileLayer('Stamen Toner Lite', name='Base Map (Simple)').add_to(m)
    
    if DF_DATA.empty:
        print("[CRITICAL ❌] DF_DATA 为空，无法生成地图。")
        return html.Div("❌ 数据为空，无法生成地图。"), None, None, {
            "fare": "DF_DATA empty",
            "volume": "DF_DATA empty"
        }

    # 2. KPI 图层 (已将 Colormap 排除在 FeatureGroup 之外)
    fare_fg, fare_colormap, fare_status = _add_kpi_layer(
        m, "Avg Fare Routes (票价)", FARE_COL, 'mean', True
    )
    volume_fg, volume_colormap, volume_status = _add_kpi_layer(
        m, "Total Passenger Volume Routes (客运量)", PASSENGER_COL, 'sum', False
    )
    
    print("\n--- KPI 图层生成状态摘要 ---")
    print(f"票价图层状态 (Fare Status): {fare_status}")
    print(f"客运量图层状态 (Volume Status): {volume_status}")
    print("---------------------------------")


    # 3. 机场 marker
    airport_fg = folium.FeatureGroup(name='Airport Markers', show=True)

    num_airports_drawn = 0
    for code, (lat, lon) in AIRPORT_COORDS.items():
        airport_data = DF_DATA.query("Origin == @code or Dest == @code")
        airport_fare = airport_data[FARE_COL].mean()
        
        popup_text = (
            f"{code}<br>Avg Fare: ${airport_fare:.2f}"
            if not np.isnan(airport_fare)
            else code
        )
        
        if airport_data.empty:
            print(f"[DEBUG ⚠️] 机场 {code} 在 DF_DATA 中无起降记录。")
        else:
             print(f"[DEBUG ✅] 机场 {code}: 平均票价 ${airport_fare:.2f}。")
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=7,                   # 大小合适
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.9,
            popup=popup_text,
            tooltip=code,
        ).add_to(airport_fg)
        
        num_airports_drawn += 1

    airport_fg.add_to(m)
    print(f"✅ 成功绘制 {num_airports_drawn} 个机场 Marker。")

    # 4. ------------------------------------------------------------------
    # 📢 关键修复：统一添加 Colormaps (Legend) 和 LayerControl (解决 topright 错误)
    # ------------------------------------------------------------------
    # 统一添加 Colormaps (Legend) 到地图根部
    if fare_colormap:
        fare_colormap.add_to(m)
        print("✅ 票价 Colormap 已添加到地图。")
    if volume_colormap:
        volume_colormap.add_to(m)
        print("✅ 客运量 Colormap 已添加到地图。")

    # 显式添加 LayerControl
    folium.LayerControl(collapsed=True).add_to(m)
    print("✅ LayerControl 已显式添加到地图。")


    # 5. ------------------------------------------------------------------
    # 📢 关键修复：注入 JavaScript 强制 Leaflet 重新计算大小 (保持不变)
    # ------------------------------------------------------------------
    map_id = m.get_name() 
    js_fix = f"""
        // 强制 Leaflet 重新计算地图大小，解决在动态 Iframe (如 Dash) 中不显示的问题
        setTimeout(function() {{
            if (window.{map_id}) {{
                window.{map_id}.invalidateSize();
                // 打印到浏览器控制台，帮助进一步调试
                console.log("Folium Fix: invalidateSize triggered for {map_id}"); 
            }}
        }}, 500); // 延迟 500ms 确保 Iframe 和 DOM 已经完全加载
        """
    m.get_root().script.add_child(folium.Element(js_fix))
    print(f"✅ 已注入 JavaScript 修复代码 (invalidateSize) 到地图 ID: {map_id}")
    # ------------------------------------------------------------------


    # 6. 渲染 HTML
    map_html = m.get_root().render()

    map_component = html.Iframe(
        id="folium-map-iframe",
        srcDoc=map_html,
        style={"width": "100%", "height": "600px", "border": "none"}
    )

    status = {"fare": fare_status, "volume": volume_status}
    
    print("🎉 地图 HTML 字符串已生成，并封装到 Dash Iframe 组件。")
    print("========================================================\n")


    return map_component, fare_colormap, volume_colormap, status