# src/components/layout.py

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc 

# 1. 定义常量
ROUTE_OPTIONS = [
    {"label": "LAX - LAS", "value": "LAX-LAS"},
    {"label": "DEN - JFK", "value": "DEN-JFK"},
    {"label": "ORD - DFW", "value": "ORD-DFW"},
    {"label": "LAX - SFO", "value": "LAX-SFO"},
    {"label": "JFK - MCO", "value": "JFK-MCO"},
    {"label": "SFO - SEA", "value": "SFO-SEA"},
]

# 2. 定义布局函数
def create_layout(app: Dash) -> html.Div:
    app.title = "Flight Market Analysis Dashboard"

    # 主下拉菜单选项
    analysis_options = [
        {"label": "1. Average Fare Trend (平均票价趋势)", "value": "fare-trend"},
        {"label": "2. Passenger Volume Trend (总客运量趋势)", "value": "volume-trend"},
        {"label": "3. Price Forecast (何时购买机票/价格预测)", "value": "price-forecast"},
        {"label": "4. Market Map (市场概览地图)", "value": "market-map"},
    ]

    return dbc.Container( 
        className="app-div",
        children=[
            html.H1(app.title, className="text-center my-4"),
            html.Hr(),

            dbc.Row([
                # 左侧：主分析类型选择
                dbc.Col(
                    html.Div(
                        children=[
                            html.Label("选择分析类型:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="analysis-type-dropdown",
                                options=analysis_options,
                                value="fare-trend",     
                                clearable=False,
                                placeholder="选择分析功能",
                            )
                        ],
                        className="p-3 border rounded h-100"
                    ),
                    md=6, 
                ),
                
                # 右侧：路线选择容器 (仅适用于趋势和预测)
                dbc.Col(
                    html.Div(
                        id="route-selection-container",
                        children=[
                            html.Label("选择路线 (Origin-Dest):", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="route-dropdown",
                                options=ROUTE_OPTIONS,
                                value=ROUTE_OPTIONS[0]["value"], 
                                clearable=False,
                                placeholder="选择航线 (Origin-Dest)",
                            )
                        ],
                        className="p-3 border rounded h-100"
                    ),
                    md=6, 
                ),
            ], className="g-4 mb-4"), 

            # ------------------------------------------------------------------
            # 🆕 新增：地图 KPI 切换控件 (用于 Plotly Mapbox 方案，代替 LayersControl)
            # 默认隐藏，在 callbacks.py 中切换到 'market-map' 时显示
            # ------------------------------------------------------------------
            dbc.Row(
                dbc.Col(
                    html.Div(
                        id='map-kpi-control',
                        children=[
                            dbc.Label("地图显示 KPI:", html_for="map-kpi-dropdown", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='map-kpi-dropdown',
                                options=[
                                     {'label': '平均票价', 'value': 'fare'}, 
                                     {'label': '客运总量', 'value': 'volume'}
                                ],
                                value='fare',
                                clearable=False
                            ),
                        ],
                        # ⚠️ 关键：默认隐藏，由回调控制显示
                        style={'display': 'none', 'width': '300px', 'margin-bottom': '15px'}, 
                        className="p-3 border rounded"
                    ),
                    # 将其放在一列中并限制宽度，使其看起来像一个控件
                    md=4 
                ), 
                justify="start", # 确保控件靠左对齐
                className="mb-4"
            ),
            # ------------------------------------------------------------------


            # Chart and Output Area
            html.Div(
                id="content-output",
                className="mt-4 border p-4 rounded",
                children=[
                    html.H3("分析结果将显示在此处", className="text-center text-muted")
                ]
            )
        ],
        fluid=True, 
    )