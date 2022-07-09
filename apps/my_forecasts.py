from dash.dependencies import Input, Output, State
from dash_core_components.Loading import Loading
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_table as dt
import dash_daq as daq
from apps import common_components
from core import decline_curve_analysis as dca
from app import app
import plotly.graph_objects as go
import json
from core import database as db
import pandas as pd


#------------------------------------------------------------------------------
# Layout
#------------------------------------------------------------------------------
layout = html.Div([
    # Store user forecasts
    dcc.Store(id='my_forecasts', storage_type='session'),

    # Title and logo row
    dbc.Row([
        # Title
        dbc.Col(
            dbc.Card([
                dbc.CardHeader([
                    html.H1('Mis pronósticos', className='card-title')]
                )],
                className='w-75'
            ),
            style = {'paddingTop': '10px'}
        ),
        
        # Logo
        dbc.Col([
            common_components.logo,
            common_components.social_media_buttons],
            width=2
        )
    ]),

    # DataTable row
    dbc.Row([
        dbc.Col([
            dbc.Button(
                ['Consultar DB'],
                id = 'query-my-forecasts',
                color = 'light',
                style = {'display': 'inline-block', 'font-family': 'sans-serif'}
            ),
            
            html.Div([
                html.P(id = 'my-fc-tooltip', className = "fas fa-question")],
                style = {
                    'textAlign': 'left',
                    'display': 'inline-block',
                    'padding-left': '5px'}
            ),

            dbc.Tooltip([
                html.P(
                    ['X: Ocultar pronóstico'],
                    style = {'margin': '0'}
                ),

                html.P(
                    ['■: Graficar pronóstico'],
                    style = {'margin': '0'}
                ),

                html.Br(),
                
                html.P(
                    ['Podés filtrar los campos numéricos usando los símbolos >, \
                    <, =, >=, <='],
                    style = {'margin': '0'}
                )],

                target = "my-fc-tooltip",
                style = {'textAlign': 'left'}
            )
        ])
    ]),

    dbc.Row([
        dbc.Col([
            # DataTable with forecasts
            dcc.Loading(
                children=[
                    dt.DataTable(
                    id = 'my_forecasts_table',
                    columns = [
                        {'name': 'Fecha pronos', 'id': 'savedate'},
                        {'name': 'Pozo:Form', 'id': 'Pozo_Form'},
                        {'name': 'Modelo DCA', 'id': 'DCA_model'},
                        {'name': 'b', 'id': 'b'},
                        {'name': 'D_hyp', 'id': 'D_hyp'},
                        {'name': 'D_exp', 'id': 'D_exp'},
                        {'name': 'Tipo pronos', 'id': 'Tipo_Pronos'},
                        {'name': 'ID', 'id': 'ID_Pronos'}
                    ],
                    filter_action = 'native',
                    row_deletable = True,
                    row_selectable = 'multi',
                    page_size = 20,
                    style_table={'minWidth': '100%', 'overflowX': 'auto'},
                    fixed_columns={'headers': True, 'data': 2},
                    style_header={'fontWeight': 'bold'},
                    style_cell_conditional=[
                        {'if': {'column_id': 'savedate'},
                        'width': '15%'}
                    ]
                    )
                ],
                type='dot',
                color='#2A5261',
                fullscreen=False
            )]
        )
    ]),

    html.Br(),

    # Graphs controls row
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H6('Lineal',
                    style={'display':'inline-block', 'paddingRight': 5}
                ),

                daq.ToggleSwitch(
                    id = 'my-fc-log-scale',
                    size=35,
                    value = True,
                    style={'display':'inline-block'}
                ),

                html.H6('Log',
                    style={'display':'inline-block', 'paddingLeft': 5}
                )],
                
                style={'display':'inline-block', 'float': 'right'}
            )]
        )
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            # Oil rate graph
                            dcc.Loading(
                                children = [
                                    dcc.Graph(
                                        id = 'my_oil_rates',
                                        style = {"height": 450})
                                ],
                                type = 'dot',
                                color = '#2A5261',
                                fullscreen = False
                            )],
                            xs=12,
                            sm=12,
                            md=12,
                            lg=6
                        ),
                    
                        dbc.Col([
                            # Oil cumulative graph
                            dcc.Loading(
                                children = [
                                    dcc.Graph(
                                        id = 'my_oil_cumulatives',
                                        style = {"height": 450}
                                    )
                                ],
                                type = 'dot',
                                color = '#2A5261',
                                fullscreen = False
                            )],
                            xs=12,
                            sm=12,
                            md=12,
                            lg=6
                        )]
                    )],

                    label = "Petróleo"
                ),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            # Gas rate graph
                            dcc.Loading(
                                children = [
                                    dcc.Graph(
                                        id = 'my_gas_rates',
                                        style = {"height": 450})
                                ],
                                type = 'dot',
                                color = '#2A5261',
                                fullscreen = False
                            )],
                            xs=12,
                            sm=12,
                            md=12,
                            lg=6
                        ),
                    
                        dbc.Col([
                            dcc.Loading(
                                children = [
                                    dcc.Graph(
                                        id = 'my_gas_cumulatives',
                                        style = {"height": 450}
                                    )
                                ],
                                type = 'dot',
                                color = '#2A5261',
                                fullscreen = False
                            )],
                            xs=12,
                            sm=12,
                            md=12,
                            lg=6
                        )]
                    )],

                    label = "Gas"
                )]
            )]
        )
    ])
])

#------------------------------------------------------------------------------
# Callbacks
#------------------------------------------------------------------------------
@app.callback(
    [Output('my_oil_rates', 'figure'),
    Output('my_oil_cumulatives', 'figure'),
    Output('my_gas_rates', 'figure'),
    Output('my_gas_cumulatives', 'figure'),
    Output('my_forecasts', 'data')],

    [Input('my_forecasts_table', 'derived_virtual_data'),
    Input('my_forecasts_table', 'derived_virtual_selected_rows'),
    Input('my-fc-log-scale', 'value')],

    [State('session', 'data'),
    State('my_forecasts', 'data')]
)
def update_my_plots(table_data, selected_data, log_scale, session, my_forecasts_json):
    '''
    TODO: AGREGAR DOCSTRING
    '''

    # Read current state of my forecasts
    if (my_forecasts_json is not None) and len(json.loads(my_forecasts_json)):
        my_forecasts = {'df': pd.DataFrame(json.loads(my_forecasts_json))}
        my_forecasts['ids'] = my_forecasts['df']['ID_Pronos'].unique()

    else:
        my_forecasts = {'ids': []}
        my_forecasts['df'] = pd.DataFrame({})

    
    qo_fig = go.Figure()
    cumo_fig = go.Figure()

    qo_fig.update_layout(
        margin = dict(l=20, r=20, b=20, t=35),
        title = {'text': f'Caudal de Petróleo', 'y': 0.96, 'x': 0.5,
            'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title = 'Días',
        yaxis_title = 'qo [m3/d]',
        showlegend = False,
    )

    cumo_fig.update_layout(
        margin = dict(l=20, r=20, b=20, t=35),
        title = {'text': f'Acumulada de Petróleo', 'y': 0.96, 'x':0.5,
            'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title = 'Días',
        yaxis_title = 'Np [m3]',
        showlegend = False, 
    )

    qg_fig = go.Figure()
    cumg_fig = go.Figure()

    qg_fig.update_layout(
        margin = dict(l=20, r=20, b=20, t=35),
        title = {'text': f'Caudal de Gas', 'y': 0.96, 'x': 0.5,
            'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title = 'Días',
        yaxis_title = 'qg [Mm3/d]',
        showlegend = False,
    )

    cumg_fig.update_layout(
        margin = dict(l=20, r=20, b=20, t=35),
        title = {'text': f'Acumulada de Gas', 'y': 0.96, 'x':0.5,
            'xanchor': 'center', 'yanchor': 'top'},
        xaxis_title = 'Días',
        yaxis_title = 'Gp [Mm3]',
        showlegend = False, 
    )

    # Get selected forecasts from DB
    if session and 'LOGGED_IN' in session and selected_data:
        session_dict = json.loads(session)

        # Selected forecasts ids
        forecasts_ids = pd.DataFrame(table_data).iloc[selected_data]['ID_Pronos']

        # Append history ids
        history_ids = pd.Series('H_' + 
            pd.unique(pd.DataFrame(table_data).iloc[selected_data]['Pozo_Form']))
        ids = pd.concat((history_ids, forecasts_ids), axis=0)

        # Query only ids not stored in session
        mask = ids.apply(lambda row: row not in my_forecasts['ids'])

        result = db.read_my_forecasts('H_P', ids[mask], session_dict)

        # Store my forecasts in session
        if my_forecasts['df'].empty:
            my_forecasts['df'] = result.copy()
        else:
            result.reset_index(drop=True, inplace=True)
            my_forecasts['df'] = pd.concat((my_forecasts['df'], result), axis=0)
            my_forecasts['df'].reset_index(drop=True, inplace=True)

        # Add traces to plot
        selected_forecasts_ids = list(ids.unique())
        wells = {}

        for forecast_id in selected_forecasts_ids:
            # Get well name
            wellname = forecast_id

            wells[wellname] = {
            'wellname': wellname,
            'well_data': my_forecasts['df'].loc[ \
                my_forecasts['df']['ID_Pronos'] == forecast_id].sort_values(by=['TdP'])
            }

            dca.add_fig_trace(qo_fig, wells[wellname], 'qo', 'history')
            dca.add_fig_trace(cumo_fig, wells[wellname], 'cumo', 'history')

            dca.add_fig_trace(qg_fig, wells[wellname], 'qg', 'history')
            dca.add_fig_trace(cumg_fig, wells[wellname], 'cumg', 'history')
    
    # Update scale
    if log_scale:
        qo_fig.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
        qg_fig.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
    else:
        qo_fig.update_yaxes(type = 'linear')
        qg_fig.update_yaxes(type = 'linear')

    return qo_fig, cumo_fig, qg_fig, cumg_fig, my_forecasts['df'].to_json()


@app.callback(
    [Output('query-my-forecasts', 'n_clicks'),
    Output('my_forecasts_table', 'data'),
    Output('my-fc-db-toast', 'data')],

    Input('query-my-forecasts', 'n_clicks'),

    State('session', 'data')
)
def update_my_forecasts_table(query_button_click, session):
    '''
    TODO: COMPLETAR DOCSTRING
    '''

    toast_header = 'Consultar DB'
    my_forecasts_table = []

    # If button is clicked, query DB
    if query_button_click:
        try:
            if session and 'LOGGED_IN' in session: session_dict = json.loads(session)

            result = db.read_my_forecasts('parameters', None, session_dict)
            
            # Build data table with my forecasts ids
            params = [dca.get_params_from_forecast_ID(x) for x in result['ID_Pronos']]

            for forecast_id in params:
                if len(forecast_id) == 8:
                    forecast_id.insert(7, None)
                    forecast_id.insert(8, None)
                    forecast_id.insert(9, None)

            df_table = pd.DataFrame(params, columns=['Company', 'savedate',
                'DCA_model', 'b', 'D_hyp', 'D_exp', 'Pozo_Form', 'Norm', 'Norm_type', 'Norm_value', 'Tipo_Pronos'])
            df_table['savedate'] = df_table['savedate'].apply(
                lambda x: '-'.join((x[:4], x[4:6], x[6:])))
            df_table['b'] = df_table['b'].apply(lambda x: x.split(':')[1])
            df_table['D_hyp'] = df_table['D_hyp'].apply(lambda x: x.split(':')[1])
            df_table['D_exp'] = df_table['D_exp'].apply(lambda x: x.split(':')[1])
            df_table = pd.concat([df_table, result['ID_Pronos']], axis=1)

            my_forecasts_table = df_table.to_dict('records')

            toast_msg = 'Pronósticos cargados desde DB correctamente.'
            toast_icon = "success"
            toast_duration = 4000 # Milisecs

        except Exception as err:
            toast_msg = f'Ocurrió un error al cargar los pronósticos de DB. [{err}]'
            toast_duration = None
            toast_icon = "warning"

        open_toast = True
    else:
        return 0, my_forecasts_table, None

    toast = {
        'db-msg': {
            'children': toast_msg
        },
        'db-toast': {
            'is_open': open_toast,
            'header': toast_header,
            'duration': toast_duration,
            'icon': toast_icon
        }
    }

    return 0, my_forecasts_table, json.dumps(toast)