import folium 
import pandas as pd 
import os 
import numpy as np 
import branca.colormap as cm 
from dash import html
from src.data_loader import DF_DATA, FARE_COL, ROUTE_COL, PASSENGER_COL 

map_html_path = os.path.join(os.getcwd(), 'assets', 'folium_map.html')

airport_coords = {
    "LAX": (33.9416, -118.4090), "LAS": (36.0800, -115.1522),
    "DEN": (39.8500, -104.6740), "JFK": (40.6413, -73.7781),
    "ORD": (41.9742, -87.9073), "DFW": (32.8998, -97.0403),
    "SFO": (37.6213, -122.3790), "SEA": (47.4502, -122.3088),
    "MCO": (28.4312, -81.3080),
}

od_pairs = [
    ("LAX", "LAS"), ("DEN", "JFK"), ("ORD", "DFW"), 
    ("LAX", "SFO"), ("JFK", "MCO"), ("SFO", "SEA"),
]

def _add_kpi_layer(m, kpi_name, kpi_col, agg_func, is_fare):
    """calculate kpi stats and add a featuregroup layer to the map"""
    
    route_stats = DF_DATA.groupby(['Origin', 'Dest'])[kpi_col].agg(agg_func).reset_index()
    route_stats['Route'] = route_stats['Origin'] + '-' + route_stats['Dest']
    route_stats.rename(columns={kpi_col: 'KPI_Value'}, inplace=True)
    
    required_routes = [f"{o}-{d}" for o, d in od_pairs]
    kpi_values = route_stats[route_stats['Route'].isin(required_routes)]['KPI_Value'].dropna()
    
    if kpi_values.empty:
        status_msg = f"invalid data: {kpi_name} layer has no valid kpi values"
        return None, None, status_msg
        
    min_val = kpi_values.min()
    max_val = kpi_values.max()

    if min_val == max_val:
        max_val = min_val + 1 
        
    fg = folium.FeatureGroup(name=kpi_name, show=is_fare) 
    caption = "Average Market Fare ($)" if is_fare else "Total Passenger Volume"
    
    if is_fare:
        colormap = cm.linear.RdYlGn_04.scale(max_val, min_val) 
        unit = '$'
    else:
        colormap = cm.linear.RdYlGn_04.scale(min_val, max_val)
        unit = ''
        
    colormap.caption = caption 

    min_weight, max_weight = 2, 8 
    range_diff = max_val - min_val
    if range_diff == 0: range_diff = 1 
            
    num_routes_drawn = 0
    for origin, dest in od_pairs:
        route_str = f"{origin}-{dest}"
        route_data = route_stats.query("Origin == @origin and Dest == @dest")
        
        if not route_data.empty:
            kpi_value = route_data['KPI_Value'].iloc[0]
            
            if pd.isna(kpi_value): 
                continue 
                 
            line_color = colormap(kpi_value)
            
            normalized_kpi = (kpi_value - min_val) / range_diff
            line_weight = min_weight + normalized_kpi * (max_weight - min_weight)
            
            tooltip_val = f"{kpi_value:.2f}" if is_fare else f"{kpi_value:,.0f}"
            tooltip_text = f"Route: {route_str}<br>{caption}: {unit}{tooltip_val}"
            
            folium.PolyLine(
                [airport_coords[origin], airport_coords[dest]],
                color=line_color,
                weight=line_weight,
                opacity=0.8,
                tooltip=tooltip_text
            ).add_to(fg)
            
            num_routes_drawn += 1
            
    fg.add_to(m)
    status_msg = f"successfully generated {num_routes_drawn} routes"
    return fg, colormap, status_msg

def create_folium_map():
    
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4, tiles="CartoDB positron")
    folium.TileLayer('Stamen Toner Lite', name='base map (simple)').add_to(m)
    
    if DF_DATA.empty:
        return html.Div("data empty, cannot generate map"), None, None, {
            "fare": "DF_DATA empty",
            "volume": "DF_DATA empty"
        }

    fare_fg, fare_colormap, fare_status = _add_kpi_layer(
        m, "avg fare routes", FARE_COL, 'mean', True
    )
    volume_fg, volume_colormap, volume_status = _add_kpi_layer(
        m, "total passenger volume routes", PASSENGER_COL, 'sum', False
    )

    airport_fg = folium.FeatureGroup(name='airport markers', show=True)
    for code, (lat, lon) in airport_coords.items():
        airport_data = DF_DATA.query("Origin == @code or Dest == @code")
        airport_fare = airport_data[FARE_COL].mean()
        
        popup_text = (
            f"{code}<br>Avg Fare: ${airport_fare:.2f}"
            if not np.isnan(airport_fare)
            else code
        )
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.9,
            popup=popup_text,
            tooltip=code,
        ).add_to(airport_fg)

    airport_fg.add_to(m)

    if fare_colormap:
        fare_colormap.add_to(m)
    if volume_colormap:
        volume_colormap.add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)

    map_id = m.get_name() 
    js_fix = f"""
        setTimeout(function() {{
            if (window.{map_id}) {{
                window.{map_id}.invalidateSize();
            }}
        }}, 500);
        """
    m.get_root().script.add_child(folium.Element(js_fix))

    map_html = m.get_root().render()

    map_component = html.Iframe(
        id="folium-map-iframe",
        srcDoc=map_html,
        style={"width": "100%", "height": "600px", "border": "none"}
    )

    status = {"fare": fare_status, "volume": volume_status}

    return map_component, fare_colormap, volume_colormap, status
