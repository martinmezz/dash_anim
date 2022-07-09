import dash
import dash_bootstrap_components as dbc


FA = "https://use.fontawesome.com/releases/v5.12.1/css/all.css"

app = dash.Dash(__name__,
    external_stylesheets = [dbc.themes.MINTY, FA],
    suppress_callback_exceptions = True)

app.title = 'Oil & Gas Dash'

server = app.server