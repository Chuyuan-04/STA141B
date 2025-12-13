# main.py

from dash import Dash
import dash_bootstrap_components as dbc 
from src.components.layout import create_layout
from src.callbacks import register_callbacks 

def main() -> None:
    app = Dash(
        __name__, 
        external_stylesheets=[dbc.themes.FLATLY], 
        suppress_callback_exceptions=True,
    )
    
    app.layout = create_layout(app)
    
    register_callbacks(app)
    
    app.run(debug=True) 


if __name__ == "__main__":
    main()