import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from apps import common_components


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
        '404',
        style = {
            'textAlign': 'center',
            'paddingTop': '25px'
        }
    ),

    # Subtitle
    html.H2('Not found', style = {'textAlign': 'center'}),

    html.Br(),

    html.Div([
        html.Img(
            src = '/assets/404.png',
            height = 400
        )],
        style={'textAlign': 'center'}
    ),]
)