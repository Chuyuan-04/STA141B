# src/callbacks.py

from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from src.data_loader import (
    generate_fare_trend_plot, 
    generate_price_forecast_plot,
    generate_passenger_volume_plot, 
)
# Map generator
from src.folium_map_generator import create_folium_map 
from dash import callback
import pandas as pd 


def register_callbacks(app: Dash):
    
    # 1. Visibility control callback
    @app.callback(
        [Output('route-selection-container', 'style'),
         Output('map-kpi-control', 'style')],
        Input('analysis-type-dropdown', 'value'),
    )
    def update_controls_visibility(analysis_type: str):
        route_style = {} 
        map_kpi_style = {'display': 'none'} 
        
        if analysis_type == 'market-map':
            route_style = {'display': 'none'}
            
        return route_style, map_kpi_style

    # 2. Main content callback
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

        # Market map analysis type
        if analysis_type == 'market-map':
            
            map_component, fare_colormap, volume_colormap, status_diagnostics = create_folium_map()
            
            # Use vmin / vmax from colormap
            if fare_colormap:
                fare_legend_html = (
                    f"**Avg Fare:** low ({fare_colormap.vmin:.0f}, Green) → "
                    f"high ({fare_colormap.vmax:.0f}, Red)"
                )
            else:
                fare_legend_html = "**Avg Fare:** Failed to display"
                 
            if volume_colormap:
                # Format as integers with comma separators
                volume_legend_html = (
                    f"**Total Volume:** low ({volume_colormap.vmin:,.0f}, Red) → "
                    f"high ({volume_colormap.vmax:,.0f}, Green)"
                )
            else:
                volume_legend_html = "**Total Volume:** Failed to display"
            
            content = [
                html.H3("Overview of Major Routes", className="mb-4 text-center"),
                
                dbc.Alert(
                    [
                        html.H5("KPI Legend", className="alert-heading"),
                        html.P(fare_legend_html),
                        html.P(volume_legend_html, className="mb-0"),
                        html.P(
                            "Use the layer control in the top-right corner to switch between map layers.",
                            className="small mt-2"
                        )
                    ],
                    color="light",
                    className="mb-3"
                ),
                
                dbc.Alert(
                    [
                        html.H5("Map Diagnostics Status", className="alert-heading"),
                        html.P(f"Fare route layer: {status_diagnostics['fare']}"),
                        html.P(f"Passenger volume route layer: {status_diagnostics['volume']}"),
                    ],
                    color="warning",
                    className="mb-3"
                ),
                
                # Embed Folium map
                html.Div(map_component, id='main-analysis-map-container'),
            ]
            return content, default_kpi_options, default_kpi_value

        # Other analysis logic
        if not route:
            return (
                dbc.Alert("Please select a route to display the results.", color="warning"),
                default_kpi_options,
                default_kpi_value
            )

        elif analysis_type == 'fare-trend':
            graph_figure = generate_fare_trend_plot(route)
            title = f"Analysis Results: Average Fare Trend – {route}"
            
        elif analysis_type == 'volume-trend':
            graph_figure = generate_passenger_volume_plot(route)
            title = f"Analysis Results: Total Passenger Volume Trend – {route}"
            
        elif analysis_type == 'price-forecast':
            graph_figure = generate_price_forecast_plot(route)
            title = f"Analysis Results: Price Forecast – {route}"
            
        else:
            return (
                dbc.Alert("Please select an analysis type.", color="secondary"),
                default_kpi_options,
                default_kpi_value
            )
        
        content = [
            html.H3(title, className="mb-4 text-center"),
            dcc.Graph(figure=graph_figure, id='main-analysis-graph'),
            html.P(
                "The chart has been updated. Try switching routes or analysis types.",
                className="text-muted small mt-2"
            )
        ]
        
        return content, default_kpi_options, default_kpi_value
