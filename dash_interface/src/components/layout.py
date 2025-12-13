# src/components/layout.py

from dash import Dash, html, dcc
import dash_bootstrap_components as dbc 

ROUTE_OPTIONS = [
    {"label": "LAX - LAS", "value": "LAX-LAS"},
    {"label": "DEN - JFK", "value": "DEN-JFK"},
    {"label": "ORD - DFW", "value": "ORD-DFW"},
    {"label": "LAX - SFO", "value": "LAX-SFO"},
    {"label": "JFK - MCO", "value": "JFK-MCO"},
    {"label": "SFO - SEA", "value": "SFO-SEA"},
]

# 2. layout function
def create_layout(app: Dash) -> html.Div:
    app.title = "Flight Market Analysis Dashboard"

    # options for the main
    analysis_options = [
        {"label": "1. Average Fare Trend", "value": "fare-trend"},
        {"label": "2. Passenger Volume Trend", "value": "volume-trend"},
        {"label": "3. Price Forecast", "value": "price-forecast"},
        {"label": "4. Market Map", "value": "market-map"},
    ]

    return dbc.Container( 
        className="app-div",
        children=[
            html.H1(app.title, className="text-center my-4"),
            html.Hr(),

            dbc.Row([
                #left
                dbc.Col(
                    html.Div(
                        children=[
                            html.Label("Analysis Type:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="analysis-type-dropdown",
                                options=analysis_options,
                                value="fare-trend",     
                                clearable=False,
                                placeholder="Select Analysis Function",
                            )
                        ],
                        className="p-3 border rounded h-100"
                    ),
                    md=6, 
                ),
                
                # right
                dbc.Col(
                    html.Div(
                        id="route-selection-container",
                        children=[
                            html.Label("Select (Origin-Dest):", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="route-dropdown",
                                options=ROUTE_OPTIONS,
                                value=ROUTE_OPTIONS[0]["value"], 
                                clearable=False,
                                placeholder="Select (Origin-Dest)",
                            )
                        ],
                        className="p-3 border rounded h-100"
                    ),
                    md=6, 
                ),
            ], className="g-4 mb-4"), 


            dbc.Row(
                dbc.Col(
                    html.Div(
                        id='map-kpi-control',
                        children=[
                            dbc.Label("Map KPI:", html_for="map-kpi-dropdown", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='map-kpi-dropdown',
                                options=[
                                     {'label': 'Average Fare', 'value': 'fare'}, 
                                     {'label': 'Volume', 'value': 'volume'}
                                ],
                                value='fare',
                                clearable=False
                            ),
                        ],

                        style={'display': 'none', 'width': '300px', 'margin-bottom': '15px'}, 
                        className="p-3 border rounded"
                    ),

                    md=4 
                ), 
                justify="start", 
                className="mb-4"
            ),
            # ------------------------------------------------------------------


            # Chart and Output Area
            html.Div(
                id="content-output",
                className="mt-4 border p-4 rounded",
                children=[
                    html.H3("Results", className="text-center text-muted")
                ]
            )
        ],
        fluid=True, 
    )