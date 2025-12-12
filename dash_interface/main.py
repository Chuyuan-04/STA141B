# main.py (Final Folium Version)

from dash import Dash
import dash_bootstrap_components as dbc 
from src.components.layout import create_layout
from src.callbacks import register_callbacks 

def main() -> None:
    # 启用 Bootstrap 样式, 抑制初始回调异常
    app = Dash(
        __name__, 
        external_stylesheets=[dbc.themes.FLATLY], 
        suppress_callback_exceptions=True,
    )
    
    app.layout = create_layout(app)
    
    # 📢 关键修改：调用正确的函数名
    register_callbacks(app)
    
    app.run(debug=True) 


if __name__ == "__main__":
    main()