# src/callbacks.py (最终 Folium 整合版本)

from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from src.data_loader import (
    generate_fare_trend_plot, 
    generate_price_forecast_plot,
    generate_passenger_volume_plot, 
)
# 📢 关键修复 1: 导入最终的地图生成器
from src.folium_map_generator import create_folium_map 
from dash import callback
import pandas as pd # 导入 pandas 以便处理 colormap 检查

# 📢 关键修复 2: 注册函数名称应该与 main.py 中的导入匹配
def register_callbacks(app: Dash):
    
    # 1. Visibility Control Callback (保持不变)
    @app.callback(
        [Output('route-selection-container', 'style'),
         Output('map-kpi-control', 'style')],
        Input('analysis-type-dropdown', 'value'),
    )
    def update_controls_visibility(analysis_type: str):
        route_style = {} 
        map_kpi_style = {'display': 'none'} # Folium 方案隐藏这个
        
        if analysis_type == 'market-map':
            route_style = {'display': 'none'}
            
        return route_style, map_kpi_style

    # 2. Main Content Callback
    @app.callback(
        [Output('content-output', 'children'),
         Output('map-kpi-dropdown', 'options'),
         Output('map-kpi-dropdown', 'value')],
        [Input('analysis-type-dropdown', 'value'),
         Input('route-dropdown', 'value')],
        prevent_initial_call=False 
    )
    def update_content(analysis_type: str, route: str):
        
        default_kpi_options = [{'label': 'Fare', 'value': 'fare'}]
        default_kpi_value = 'fare'

        # --- Market Map Analysis Type (使用 Folium Iframe) ---
        if analysis_type == 'market-map':
            
            # 📢 关键修复 3: 调用正确的函数并接收四个返回值
            map_component, fare_colormap, volume_colormap, status_diagnostics = create_folium_map()
            
            # (2) 渲染图例 和 诊断信息
            
            # 使用 Colormap 的 vmin/vmax 和颜色逻辑来构建图例文字
            if fare_colormap:
                 fare_legend_html = f"**平均票价 (Avg Fare):** 低 ({fare_colormap.vmin:.0f}, 绿色) → 高 ({fare_colormap.vmax:.0f}, 红色)"
            else:
                 fare_legend_html = f"**平均票价:** 无法计算图例，请检查数据。"
                 
            if volume_colormap:
                # 确保格式化为整数，并使用逗号分隔符
                volume_legend_html = f"**总客运量 (Total Volume):** 低 ({volume_colormap.vmin:,.0f}, 红色) → 高 ({volume_colormap.vmax:,.0f}, 绿色)"
            else:
                volume_legend_html = f"**总客运量:** 无法计算图例，请检查数据。"
            
            content = [
                html.H3("核心航线市场概览 (Folium/Leaflet)", className="mb-4 text-center"),
                
                dbc.Alert(
                    [
                        html.H5("KPI 颜色/粗细图例", className="alert-heading"),
                        html.P(fare_legend_html),
                        html.P(volume_legend_html, className="mb-0"),
                        html.P("使用地图右上角的 Layer Control 切换 '票价' 和 '客运量' 图层。", className="small mt-2")
                    ],
                    color="light", className="mb-3"
                ),
                
                dbc.Alert(
                    [
                        html.H5("地图诊断状态:", className="alert-heading"),
                        html.P(f"票价路线图层: {status_diagnostics['fare']}"),
                        html.P(f"客运量路线图层: {status_diagnostics['volume']}"),
                    ],
                    color="warning", className="mb-3"
                ),
                
                # 嵌入 Folium 地图
                html.Div(map_component, id='main-analysis-map-container'),
            ]
            return content, default_kpi_options, default_kpi_value

        # --- 其他分析逻辑 (保持不变) ---
        if not route:
            return dbc.Alert("请选择路线以显示结果。", color="warning"), default_kpi_options, default_kpi_value

        elif analysis_type == 'fare-trend':
            graph_figure = generate_fare_trend_plot(route)
            title = f"分析结果：平均票价趋势 - {route}"
            
        elif analysis_type == 'volume-trend':
            graph_figure = generate_passenger_volume_plot(route)
            title = f"分析结果：总客运量趋势 - {route}"
            
        elif analysis_type == 'price-forecast':
            graph_figure = generate_price_forecast_plot(route)
            title = f"分析结果：价格预测 - {route}"
            
        else:
            return dbc.Alert("请选择分析类型。", color="secondary"), default_kpi_options, default_kpi_value
        
        content = [
            html.H3(title, className="mb-4 text-center"),
            dcc.Graph(figure=graph_figure, id='main-analysis-graph'),
            html.P("图表已更新，请尝试切换路线或分析类型。", className="text-muted small mt-2")
        ]
        
        return content, default_kpi_options, default_kpi_value