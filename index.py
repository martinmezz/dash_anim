import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from app import app
from apps import home, oil_forecast, gas_forecast, maps, support, norby,norbyr, not_found,\
    common_components
from core.global_vars import *


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    # Store user info
    dcc.Store(id='session', storage_type='session'),

    # Store db toasts (used for multiple callbacks to take same output)
    dcc.Store(id='oil-db-toast', storage_type='session'),
    dcc.Store(id='oil-read-db-toast', storage_type='session'),
    dcc.Store(id='gas-db-toast', storage_type='session'),
    dcc.Store(id='gas-read-db-toast', storage_type='session'),
    dcc.Store(id='maps-db-toast', storage_type='session'),

    # Toasts
    common_components.login_toast,
    common_components.db_toast,
    common_components.user_config_toast,

    # Page content
    dbc.Container([
        common_components.header,

        common_components.navbar,

        html.Div(id = 'ribbon'),

        html.Div(id = 'page-content')],

        id = 'container',
        fluid = True
    )
])


#------------------------------------------------------------------------------
# Callbacks
#------------------------------------------------------------------------------
@app.callback(
    [Output('ribbon', 'children'),
    Output('page-content', 'children')],

    Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return home.ribbon, home.layout

    elif pathname == '/oil-forecast':
        return oil_forecast.ribbon, oil_forecast.layout

    elif pathname == '/gas-forecast':
        return gas_forecast.ribbon, gas_forecast.layout

    elif pathname == '/maps':
        return maps.ribbon, maps.layout

    elif pathname == '/support':
        return support.ribbon, support.layout

    elif pathname == '/norby':
        return norby.ribbon, norby.layout
    
    elif pathname == '/norbyr':
        return norbyr.ribbon, norbyr.layout

    else:
        return home.ribbon, not_found.layout


@app.callback(
    [Output('db-msg', 'children'),
    Output('db-toast', 'is_open'),
    Output('db-toast', 'header'),
    Output('db-toast', 'icon'),
    Output('db-toast', 'duration')],

    [Input('oil-db-toast', 'data'),
    Input('oil-read-db-toast', 'data'),
    Input('gas-db-toast', 'data'),
    Input('gas-read-db-toast', 'data'),
    Input('maps-db-toast', 'data')]
)
def show_db_toast(oil_db_toast, oil_read_db_toast, gas_db_toast, gas_read_db_toast,
    maps_db_toast):
    '''
    Controls database toast behavior.

    Params:
        - oil_db_toast (str | None): json containing toast config from oil page
        - maps_db_toast (str | None): json containing toast config from maps page

    Returns:
        - toast_msg (str): database operation result message
        - open_toast (bool): indicates whether to open toast
        - toast_header (str): toast title
        - toast_duration (int | None): miliseconds to keep toast open. 'None' keeps
            it open until user closes the toast
        - toast_icon (str): indicates the color of toast icon

    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    # Determine which view triggered the toast
    context = dash.callback_context
    if not context.triggered or (
        (maps_db_toast is None)
        and (oil_db_toast is None)
        and (oil_read_db_toast is None)
        and (gas_db_toast is None)
        and (gas_read_db_toast is None)):
        return '', False, '', 'warning', 4000
    else:
        trigger = context.triggered[0]['prop_id'].split('.')[0]

    if trigger == 'oil-db-toast':
        toast = json.loads(oil_db_toast) if oil_db_toast else dict()
    elif trigger == 'oil-read-db-toast':
        toast = json.loads(oil_read_db_toast) if oil_read_db_toast else dict()
    elif trigger == 'gas-db-toast':
        toast = json.loads(gas_db_toast) if gas_db_toast else dict()
    elif trigger == 'gas-read-db-toast':
        toast = json.loads(gas_read_db_toast) if gas_read_db_toast else dict()
    elif trigger == 'maps-db-toast':
        toast = json.loads(maps_db_toast) if maps_db_toast else dict()

    try:
        toast_msg = toast['db-msg']['children']
        open_toast = toast['db-toast']['is_open']
        toast_header = toast['db-toast']['header']
        toast_duration = toast['db-toast']['duration']
        toast_icon = toast['db-toast']['icon']
        return toast_msg, open_toast, toast_header, toast_icon, toast_duration
    except:
        return '', False, '', 'warning', 4000


#-----------------------------------------------------------------------------
# Main
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    if ENV == 'DEVELOPMENT':
        #app.run_server(debug=True, host='127.0.0.1', port='8050')
        app.run_server(debug=True, host='127.0.0.1', port='3000')
    else:
        app.run_server(debug=False, host='0.0.0.0', port='80')