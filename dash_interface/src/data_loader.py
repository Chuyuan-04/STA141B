# src/data_loader.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np # 引入 numpy 用于数据处理

# --- 全局常量定义 ---
TIME_COL = 'random_date'
FARE_COL = 'MktFare'
ROUTE_COL = 'Route'
# 修正：使用原始数据中的行级乘客列名
PASSENGER_COL = 'Passengers' 

# --- 全局变量声明 ---
DF_DATA = pd.DataFrame() 


# --- 1. 数据加载函数 ---
def load_data():
    """
    加载 cleaned_flight_data.parquet 文件，并进行基础数据准备。
    增强了错误处理和数据类型转换的鲁棒性。
    """
    global DF_DATA 
    
    data_path = 'cleaned_flight_data.parquet'
    print(f"Loading flight data from {data_path}...")
    
    try:
        df = pd.read_parquet(data_path)
        
        # --- 数据清洗和准备 ---
        
        # 1. 确保日期列是 datetime 类型
        if TIME_COL in df.columns:
            df[TIME_COL] = pd.to_datetime(df[TIME_COL])
            print(f"Column '{TIME_COL}' confirmed as datetime.")
        else:
            print(f"ERROR: Date column '{TIME_COL}' not found. Cannot proceed with time series analysis.")
            return

        # 2. 关键数值列类型转换（增强鲁棒性）
        for col in [PASSENGER_COL, FARE_COL]:
            if col in df.columns:
                # 尝试转换为数值类型，非数值设为 NaN
                df[col] = pd.to_numeric(df[col], errors='coerce') 
                # 乘客数应为整数，且不应为 NaN（使用 0 填充或删除，这里使用 0 填充）
                if col == PASSENGER_COL:
                    df[col] = df[col].fillna(0).astype(np.int64)
            
        # 3. 创建 Route 列 (Origin-Dest)
        if 'Origin' in df.columns and 'Dest' in df.columns:
             df[ROUTE_COL] = df['Origin'] + '-' + df['Dest']
        else:
            print("ERROR: 'Origin' and 'Dest' columns not found. Cannot create 'Route' column.")
            return
            
        DF_DATA = df
        print(f"Data loaded successfully. Total rows: {len(df)}")
        
    except FileNotFoundError:
        print(f"ERROR: {data_path} not found!")
    except Exception as e:
        print(f"An error occurred during data loading: {e}")

# 2. 在应用启动时，执行加载操作
load_data()


# ----------------------------------------------------
# 3. 平均票价趋势图函数 (Average Fare Trend)

def generate_fare_trend_plot(route: str):
    """
    生成平均票价趋势图 (对应选项 1: fare-trend)。
    它按月度聚合数据，并绘制趋势线。
    """
    
    if DF_DATA.empty:
        return go.Figure().update_layout(title="No data loaded.")

    origin, dest = route.split('-')
    
    # 1. 筛选特定路线的数据
    # 注意：票价通常只按单向 Route 筛选
    route_df = DF_DATA.query("Origin == @origin and Dest == @dest").copy()
    
    if route_df.empty:
        return go.Figure().update_layout(title=f"No data found for route: {route}")

    # 2. 按月度（'M'）计算平均票价
    # 注意：这里可能会出现 FutureWarning，建议在终端中忽略或在代码中替换为 'ME'
    agg_df = route_df.set_index(TIME_COL).resample('M')[FARE_COL].mean().reset_index()
    agg_df.rename(columns={FARE_COL: 'AvgFare'}, inplace=True)
    
    # 3. 创建 Plotly 线图
    fig = px.line(
        agg_df, 
        x=TIME_COL, 
        y='AvgFare',
        title=f"Market Fare Trend: {origin} → {dest} (Monthly Average)",
    )
    
    fig.update_traces(mode='lines+markers', marker=dict(size=4))
    fig.update_layout(
        xaxis_title="Date", 
        yaxis_title="Average Fare ($)", 
        template="plotly_white",
        hovermode="x unified" # 统一悬停标签
    )
    
    return fig

# ----------------------------------------------------
# 4. 客运量趋势图函数 (NEW: Passenger Volume Trend)

def generate_passenger_volume_plot(route: str):
    """
    生成总客运量趋势图 (对应选项 2: volume-trend)。
    它聚合双向路线的数据，按季度求和。
    """
    
    if DF_DATA.empty:
        return px.scatter(title="No data loaded.")

    origin, dest = route.split('-')

    # 1. 双向过滤：客运量需要聚合双向流量 (LAX-JFK 和 JFK-LAX)
    plot_df = DF_DATA[
        ((DF_DATA['Origin'] == origin) & (DF_DATA['Dest'] == dest)) |
        ((DF_DATA['Origin'] == dest) & (DF_DATA['Dest'] == origin))
    ].copy()

    if plot_df.empty:
        return px.scatter(title=f"No passenger data available for route: {route}")
        
    try:
        # 2. 聚合：按年、季、方向（Origin/Dest）对行级 'Passengers' 求和
        # 聚合后的结果将包含两条线（一个方向一条）
        grouped_df = plot_df.groupby(['Year', 'Quarter', 'Origin', 'Dest'])[PASSENGER_COL].sum().reset_index()
        
        # 3. 创建 TimePoint (季度第一天) 作为 X 轴
        # 逻辑：Q1->1 (Jan), Q2->4 (Apr), Q3->7 (Jul), Q4->10 (Oct)
        grouped_df['TimePoint'] = pd.to_datetime(
            grouped_df['Year'].astype(str) + '-' +
            (grouped_df['Quarter'] * 3 - 2).astype(str) + '-01'
        )
        
        # 4. 创建 Route 标识符并重命名聚合后的列
        grouped_df[ROUTE_COL] = grouped_df['Origin'] + '-' + grouped_df['Dest']
        # 使用一个新的列名来存储聚合后的客运量总和
        sum_col_name = 'Total_Passengers_Sum'
        grouped_df.rename(columns={PASSENGER_COL: sum_col_name}, inplace=True)
        
    except KeyError as e:
        return px.scatter(title=f"数据错误：缺少时间序列分组所需的列 ({e})。")

    # 5. 创建 Plotly 线图
    fig = px.line(
        grouped_df,
        x='TimePoint',
        y=sum_col_name, 
        color=ROUTE_COL, # 按方向（Route）区分颜色
        title=f'Quarterly Total Passenger Volume Trend for {route}',
        labels={
            'TimePoint': 'Quarter',
            sum_col_name: 'Total Passengers (Sum)',
            ROUTE_COL: 'Route Direction'
        },
        template='plotly_white'
    )

    fig.update_yaxes(
        tickformat=',.0f',
        title='Total Passengers (Sum)'
    )
    
    fig.update_layout(
        xaxis_title=None,
        legend_title='Route Direction',
        hovermode="x unified"
    )

    return fig


# ----------------------------------------------------
# 5. 价格预测图函数 (Price Forecast) - 占位符

def generate_price_forecast_plot(route: str):
    """用于 Price Forecast (选项 3) - 等待实现"""
    return go.Figure().update_layout(
        title=f"Price Forecast: {route} - Model Integration Pending",
        annotations=[
            dict(
                text="下一步我们将在这里集成您的价格预测模型。",
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=14, color="gray")
            )
        ]
    )