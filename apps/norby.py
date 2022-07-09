import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from apps import common_components
import plotly.express as px
from app import app
import flask
import json

#------------------------------------------------------------------------------
# Ribbon
#------------------------------------------------------------------------------
ribbon = html.Div()
#-----------------------------------------------------------------------------
# Layout
#-----------------------------------------------------------------------------

layout = html.Div([
    # Title and logo row
    dbc.Row([
        dbc.Col([]),

        dbc.Col(),
        
        # Logo
        dbc.Col([
            common_components.logo,
            common_components.social_media_buttons],
            width=2
        )
    ]),

    html.H1(
        'norby',
        style = {
            'textAlign': 'center',
            'paddingTop': '25px'
        }
    ),

    # Subtitle
    html.H2('prueba de norby', style = {'textAlign': 'center'}),

    html.Br(),

    html.Div([
        dbc.Button("Abrir ventana modal", id="open", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader("Norberto Martín"),
                dbc.ModalBody("This is the content of the modal"),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id="modal",
            is_open=False,
        ),
    ]),

    html.Br(),

    html.Div([
        html.H4('Animated GDP and population over decades'),
        html.P("Select an animation:"),
        dcc.RadioItems(
            id='animations-x-selection',
            options=["GDP - Scatter", "Population - Bar"],
            value='GDP - Scatter',
        ),
        dcc.Loading(dcc.Graph(id="animations-x-graph"), type="cube")
    ]),

    html.Div([
        html.Img(
            src = '/assets/404.png',
            height = 400
        )],
        style={'textAlign': 'center'}
    ),]
)

@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@app.callback(
    Output("animations-x-graph", "figure"), 
    Input("animations-x-selection", "value"))
def display_animated_graph(selection):
    df =px.data.gapminder()
   # df = '/data/gapminderDataFiveYear.csv' # replace with your own data source
    animations = {
        'GDP - Scatter': px.scatter(
            df, x="gdpPercap", y="lifeExp", animation_frame="year", 
            animation_group="country", size="pop", color="continent", 
            hover_name="country", log_x=True, size_max=55, 
            range_x=[100,100000], range_y=[25,90]),
        'Population - Bar': px.bar(
            df, x="continent", y="pop", color="continent", 
            animation_frame="year", animation_group="country", 
            range_y=[0,4000000000]),
    }
    return animations[selection]