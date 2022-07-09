import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import dash_daq as daq
from app import app
from apps import common_components
from core import frac_correlation


# THIS VIEW WILL BE DEPRECATED ON THE FUTURE (WILL BE MERGED INTO MAPS)

#------------------------------------------------------------------------------
# Layout
#------------------------------------------------------------------------------
layout = html.Div([

    dbc.Row([
        # Title
        dbc.Col(
            dbc.Card([
                dbc.CardHeader([
                    html.H1('Pronósticos de petróleo', className = 'card-title'),
                    html.H4('(por correlación Fracturas-Rama)')
                ])
            ],
            className = 'w-75'),
            style = {'paddingTop': '10px'}
        ),

        # Logo
        dbc.Col([
            common_components.logo,
            common_components.social_media_buttons],
            width = 2
        )
    ]),

    html.Br(),

    # Controls title row
    dbc.Row([
        dbc.Col([
            html.H4('Datos de completación')
        ])
    ]),

    # Controls row
    dbc.Row([
        dbc.Col([
            html.H6('Número de fracturas'),

            html.Div([
                dcc.Input(id = 'fracs',
                    type = 'number',
                    placeholder = 'Inserte número entero',
                    value = 56,
                    debounce = True,
                    max = 999,
                    style = {'width': '40%'}
                )],
                style = {'paddingTop': 5}
            )],
            xl = 2
        ),

        dbc.Col([
            html.H6('Longitud de rama [m]'),

            html.Div([
                dcc.Input(id = 'lateral_length',
                    type = 'number',
                    placeholder = 'Inserte número entero',
                    value = 2800,
                    debounce = True,
                    max = 5000,
                    style = {'width': '40%'}
                )],
                style = {'paddingTop': 5}
            )],
            xl = 2
        ),

        dbc.Col([]),

        dbc.Col([])
    ]),

    # Graph toggle control
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H6('Lineal',
                    style={'display':'inline-block', 'paddingRight': 5}
                ),

                daq.ToggleSwitch(
                    id = 'frac-fc-log-scale',
                    size = 35,
                    value = True,
                    style={'display':'inline-block'}
                ),

                html.H6('Log',
                    style={'display':'inline-block', 'paddingLeft': 5}
                )],
                
                style={'display':'inline-block', 'float': 'right'}
            )],

            style={'paddingTop': 5}
        )]
    ),

    # Graphs
    dbc.Row([
        # Rate graph
        dbc.Col([
            dcc.Loading(
                children=[
                    dcc.Graph(id = 'qo_corr_graph')
                ],
                type='dot',
                color='#2A5261',
                fullscreen=False
            )],
            xs=12,
            sm=12,
            md=12,
            lg=6
        ),
    
        # Cumulative forecast row
        dbc.Col([
            dcc.Loading(
                children=[
                    dcc.Graph(id = 'cumo_corr_graph')
                ],
                type='dot',
                color='#2A5261',
                fullscreen=False
            )],
            xs=12,
            sm=12,
            md=12,
            lg=6
        )]
    )
])


#------------------------------------------------------------------------------
# Callbacks
#------------------------------------------------------------------------------
@app.callback(
    [Output('qo_corr_graph', 'figure'),
    Output('cumo_corr_graph', 'figure')],

    [Input('fracs', 'value'),
    Input('lateral_length', 'value'),
    Input('frac-fc-log-scale', 'value')])
def update_oil_graphs_fracs(fracs, lateral_length, log_scale):
    '''
    Updates rates and cumulatives graphs based on fractures and lateral length
    values.

    Params:
        fracs (float): number of fractures
        lateral_length (float): lateral length
        log_scale (str): indicates whether to set log scale or not

    Returns:
        fig_qo (go.Figure): plot of forecasted rate vs time
        fig_cumo (go.Figure): plot of forecasted cumulative vs time
    '''

    # Calculate forecasts by fracs and lateral length
    forecast = frac_correlation.calc_forecast(fracs, lateral_length)

    # Plot rates
    fig_qo = go.Figure()

    fig_qo.add_trace(
        go.Scatter(
            x = forecast['times'],
            y = forecast['qo_p10'],
            mode = 'lines',
            line = dict(color = "#6A9949", width = 0.1),
            hovertemplate = 'qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        )
    )

    fig_qo.add_trace(
        go.Scatter(
            x = forecast['times'],
            y = forecast['qo_p90'],
            fill = 'tonexty', 
            mode = 'lines',
            line = dict(color = "#6A9949", width = 0.1),
            hovertemplate = 'qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        )
    )

    fig_qo.add_trace(
        go.Scatter(
            x = forecast['times'],
            y = forecast['qo_p50'],
            mode = 'lines',
            line = dict(color = "#6A9949"),
            hovertemplate = 'qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        )
    )

    fig_qo.update_layout(
        margin = dict(l=20, r=20, b=20, t=35),
        title = {
            'text': f'Caudal de petróleo pronosticado',
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title = 'Días [d]',
        yaxis_title = f'Caudal [m3/d]',
        height = 600,
        showlegend = False,
    )

    if log_scale:
        fig_qo.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)

    # Plot cumulatives
    fig_cumo = go.Figure()

    fig_cumo.add_trace(
        go.Scatter(
            x = forecast['times'],
            y = forecast['cumo_p10'],
            mode = 'lines',
            line = dict(color = "#6A9949", width = 0.1),
            hovertemplate = 'Qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        )
    )

    fig_cumo.add_trace(
        go.Scatter(
            x = forecast['times'],
            y = forecast['cumo_p90'],
            fill = 'tonexty', 
            mode = 'lines',
            line = dict(color = "#6A9949", width = 0.1),
            hovertemplate = 'Qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        )
    )

    fig_cumo.add_trace(
        go.Scatter(
            x = forecast['times'],
            y = forecast['cumo_p50'],
            mode = 'lines',
            line = dict(color = "#6A9949"),
            hovertemplate = 'Qo = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'
        )
    )

    fig_cumo.update_layout(
        margin = dict(l=20, r=20, b=20, t=35),
        title = {
            'text': f'Acumulada de petróleo pronosticada',
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title = 'Días [d]',
        yaxis_title = f'Acumulada [m3]',
        height = 600,
        showlegend = False,
    )
    
    return fig_qo, fig_cumo