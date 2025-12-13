# src/data_loader.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np  # import numpy for data processing

# global constants
TIME_COL = 'random_date'
FARE_COL = 'MktFare'
ROUTE_COL = 'Route'
PASSENGER_COL = 'Passengers'  # row-level passenger column from raw data

# global variables
DF_DATA = pd.DataFrame() 

# 1. data loading function
def load_data():
    """
    load cleaned_flight_data.parquet and prepare basic data.
    enhanced with error handling and type conversion robustness.
    """
    global DF_DATA 
    
    data_path = 'cleaned_flight_data.parquet'
    print(f"loading flight data from {data_path}...")
    
    try:
        df = pd.read_parquet(data_path)
        
        ## data cleaning and preparation
        
        # 1. ensure date column is datetime
        if TIME_COL in df.columns:
            df[TIME_COL] = pd.to_datetime(df[TIME_COL])
            print(f"column '{TIME_COL}' confirmed as datetime.")
        else:
            print(f"ERROR: date column '{TIME_COL}' not found. cannot proceed with time series analysis.")
            return

        # 2. key numeric columns type conversion
        for col in [PASSENGER_COL, FARE_COL]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if col == PASSENGER_COL:
                    df[col] = df[col].fillna(0).astype(np.int64)
            
        # 3. create route column (origin-dest)
        if 'Origin' in df.columns and 'Dest' in df.columns:
            df[ROUTE_COL] = df['Origin'] + '-' + df['Dest']
        else:
            print("ERROR: 'Origin' and 'Dest' columns not found. cannot create 'Route' column.")
            return
            
        DF_DATA = df
        print(f"data loaded successfully. total rows: {len(df)}")
        
    except FileNotFoundError:
        print(f"ERROR: {data_path} not found!")
    except Exception as e:
        print(f"an error occurred during data loading: {e}")

# 2. load data at app startup
load_data()


# 3. average fare trend plot function

def generate_fare_trend_plot(route: str):
    """
    generate average fare trend plot (option 1: fare-trend).
    aggregates data monthly and plots a line chart.
    """
    
    if DF_DATA.empty:
        return go.Figure().update_layout(title="no data loaded.")

    origin, dest = route.split('-')
    
    # 1. filter data for specific route
    route_df = DF_DATA.query("Origin == @origin and Dest == @dest").copy()
    
    if route_df.empty:
        return go.Figure().update_layout(title=f"no data found for route: {route}")

    # 2. aggregate by month and compute average fare
    agg_df = route_df.set_index(TIME_COL).resample('M')[FARE_COL].mean().reset_index()
    agg_df.rename(columns={FARE_COL: 'AvgFare'}, inplace=True)
    
    # 3. create plotly line chart
    fig = px.line(
        agg_df, 
        x=TIME_COL, 
        y='AvgFare',
        title=f"market fare trend: {origin} → {dest} (monthly average)",
    )
    
    fig.update_traces(mode='lines+markers', marker=dict(size=4))
    fig.update_layout(
        xaxis_title="date", 
        yaxis_title="average fare ($)", 
        template="plotly_white",
        hovermode="x unified"
    )
    
    return fig


# 4. passenger volume trend plot function

def generate_passenger_volume_plot(route: str):
    """
    generate total passenger volume trend plot (option 2: volume-trend).
    aggregates bidirectional route data and sums quarterly.
    """
    
    if DF_DATA.empty:
        return px.scatter(title="no data loaded.")

    origin, dest = route.split('-')

    # 1. bidirectional filter: aggregate both directions (origin→dest and dest→origin)
    plot_df = DF_DATA[
        ((DF_DATA['Origin'] == origin) & (DF_DATA['Dest'] == dest)) |
        ((DF_DATA['Origin'] == dest) & (DF_DATA['Dest'] == origin))
    ].copy()

    if plot_df.empty:
        return px.scatter(title=f"no passenger data available for route: {route}")
        
    try:
        # 2. aggregate by year, quarter, and direction
        grouped_df = plot_df.groupby(['Year', 'Quarter', 'Origin', 'Dest'])[PASSENGER_COL].sum().reset_index()
        
        # 3. create timepoint (first day of quarter) as x-axis
        grouped_df['TimePoint'] = pd.to_datetime(
            grouped_df['Year'].astype(str) + '-' +
            (grouped_df['Quarter'] * 3 - 2).astype(str) + '-01'
        )
        
        # 4. create route identifier and rename aggregated column
        grouped_df[ROUTE_COL] = grouped_df['Origin'] + '-' + grouped_df['Dest']
        sum_col_name = 'Total_Passengers_Sum'
        grouped_df.rename(columns={PASSENGER_COL: sum_col_name}, inplace=True)
        
    except KeyError as e:
        return px.scatter(title=f"data error: missing required column for time series grouping ({e})")

    # 5. create plotly line chart
    fig = px.line(
        grouped_df,
        x='TimePoint',
        y=sum_col_name, 
        color=ROUTE_COL,
        title=f'quarterly total passenger volume trend for {route}',
        labels={
            'TimePoint': 'quarter',
            sum_col_name: 'total passengers (sum)',
            ROUTE_COL: 'route direction'
        },
        template='plotly_white'
    )

    fig.update_yaxes(
        tickformat=',.0f',
        title='total passengers (sum)'
    )
    
    fig.update_layout(
        xaxis_title=None,
        legend_title='route direction',
        hovermode="x unified"
    )

    return fig



# 5. price forecast plot function (placeholder)

def generate_price_forecast_plot(route: str):
    """price forecast (option 3) - pending implementation"""
    return go.Figure().update_layout(
        title=f"price forecast: {route} - model integration pending",
        annotations=[
            dict(
                text="next, your price prediction model will be integrated here.",
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=14, color="gray")
            )
        ]
    )
