import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from apps import common_components
from app import app
import flask
import json


#------------------------------------------------------------------------------
# Ribbon
#------------------------------------------------------------------------------
ribbon = html.Div()

# #------------------------------------------------------------------------------
# Layout
#------------------------------------------------------------------------------
layout = html.Div([

    # Title and logo row
    dbc.Row([
        # Title
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([html.H2('FDC Dash', id='home-title')])],
                className='w-50'
            ),],
            className = 'col-no-gutters'
        ),
        
        # Logo
        dbc.Col([common_components.logo,], width=2)
    ]),
    
    # Changelog
    dbc.Card([
        dbc.CardHeader([html.H4('Versión 0.8.2', className = 'card-title')]),
        html.H6('- Pronosticos Petróleo/Gas > Se agregaron los parametros de declinacion a tablas EUR'),
        html.H6('- Pronosticos Petróleo/Gas > Posibilidad de normalizar pronósticos automáticos por longitud de rama de fractura'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.8.1', className = 'card-title')]),
        html.H6('- Pronosticos Petróleo/Gas > Tabla Información de pronósticos (Etapas de fractura, Rama lateral, EUR y EUR/etapas)'),
        html.H6('- Pronosticos Petróleo/Gas > Botones de descarga (en formato .xlsx) para tablas Información de pozos seleccionados, Información de pronósticos e Historia + pronósticos'),
        html.H6('- Corrección de bug > Las tablas no mostraban scrollbar horizontal al reescalar la ventana'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.8.0', className = 'card-title')]),
        html.H6('- Nueva interfaz de usuario'),
        html.H6('- Pronosticos Petróleo > Pronósticos manual y automático ahora son herramientas separadas'),
        html.H6('- Pronosticos Petróleo/Gas > Posibilidad de plotear pronósticos guardados en DB'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.7.7', className = 'card-title')]),
        html.H6('- Corrección de bug > Algunos pronósticos de gas devolvían error al pronosticar petróleo condensado'),
        html.H6('- Pronosticos Petróleo/Gas > Posibilidad de normalizar pronósticos automáticos por número de etapas de fractura'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.7.6', className = 'card-title')]),
        html.H6('- Corrección de bug > No se mostraban pronósticos de gas al consultar la sección Mis Pronósticos'),
        html.H6('- Pronosticos Petróleo > Posibilidad de configurar caudal límite económico'),
        html.H6('- Pronosticos Gas > Posibilidad de configurar caudal límite económico'),
        html.H6('- Pronosticos Petróleo/Gas > Se agregó la opción "Seleccionar todos" en filtros de selección de pozos'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.7.5', className = 'card-title')]),
        html.H6('- Nuevo menú de filtros'),
        html.H6('- Mejoras de layout'),
        html.H6('- Pronósticos Gas > Caudal con pronóstico automático de gas vs tiempo de producción'),
        html.H6('- Pronósticos Gas > Acumulada con pronóstico automático de gas vs tiempo de producción'),
        html.H6('- Pronósticos Gas > Tabla de datos históricos + pronósticos exportable a .xlsx'),
        html.H6('- Pronósticos Gas > Pronóstico automático de GOR vs tiempo de producción'),
        html.H6('- Pronósticos Gas > Pronóstico automático de GOR vs acumulada'),
        html.H6('- Pronósticos Gas > Pronóstico automático de petróleo vs tiempo de producción'),
        html.H6('- Pronósticos Gas > Pronóstico manual de GOR vs tiempo de producción'),
        html.H6('- Pronósticos Gas > Pronóstico manual de GOR vs acmumulada'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.7.4', className = 'card-title')]),
        html.H6('- Corrección de bug > Exportar pronósticos (DCA o correlación mapas) a DB/PowerBI no guardaba caudales correctamente'),
        html.H6('- Corrección de bug > Exportar un pronóstico (DCA o correlación mapas) a DB/PowerBI cuyo Nombre de pronóstico contenía guión bajo daba error'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.7.3', className = 'card-title')]),
        html.H6('- Pronósticos Petróleo/Gas > Tabla con información de pozos seleccionados'),
        html.H6('- Correlación Mapas > Tabla con información de pozos seleccionados'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.7.2', className = 'card-title')]),
        html.H6('- Pronósticos Petróleo > Exportar pronósticos manuales a DB'),
        html.H6('- Correlación Mapas > Exportar pronósticos a DB'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.7.1', className = 'card-title')]),
        html.H6('- Pronósticos Petróleo > Pronóstico manual de GOR vs tiempo de producción'),
        html.H6('- Pronósticos Petróleo > Pronóstico manual de GOR vs acmumulada'),
        html.H6('- Pronósticos Petróleo > GOR histórico vs acumulada histórica'),
        html.H6('- Pronósticos Petróleo > Pronóstico automático de GOR vs acumulada'),

        html.Br(),
        dbc.CardHeader([html.H4('Versión 0.7.0', className = 'card-title')]),
        html.H6('- Pronósticos Gas > Caudal histórico de gas vs tiempo de producción'),
        html.H6('- Pronósticos Gas > Caudal histórico de gas vs acumulada histórica'),
        html.H6('- Pronósticos Gas > Acumulada histórica de gas vs tiempo de producción'),
        html.H6('- Pronósticos Gas > GOR histórico vs acumulada histórica'),
        html.H6('- Pronósticos Gas > GOR histórico vs tiempo de producción'),
        html.H6('- Pronósticos Gas > Caudal histórico de petróleo vs tiempo de producción'),
        html.H6('- Pronósticos Gas > Acumulada histórica de petróleo vs tiempo de producción'),

        html.Br(),

        # Show more button
        dbc.Button(
            children = [
                html.P(
                    children = 'Más',
                    id = 'home-changelog-btn-msg',
                ),

                html.P(
                    id = 'home-changelog-btn-arrow',
                    className = "fas fa-chevron-down",
                ),
            ],

            id = 'home-changelog-button',
            color = 'light',
        ),

        dbc.Collapse([
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.6.2', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Pronóstico automático de gas vs tiempo de producción'),
            
            html.Br(),
            
            dbc.CardHeader([html.H4('Versión 0.6.1', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > GOR histórico vs tiempo de producción'),
            html.H6('- Pronósticos Petróleo > Pronóstico automático de GOR vs tiempo de producción'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.6.0', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Exportar pronósticos a DB'),
            html.H6('- Mis Pronósticos > Consulta de mis pronósticos guardados en DB'),
            html.H6('- Correlación Mapas > Caudal histórico de agua por pozo según selección'),
            html.H6('- Correlación Mapas > Acumulada histórica de agua por pozo según selección'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.5.0', className = 'card-title')]),
            html.H6('- Sección de comentarios, sugerencias y reporte de errores'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.4.0', className = 'card-title')]),
            html.H6('- Autenticación de usuarios a mediante Azure AD'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.3.6', className = 'card-title')]),
            html.H6('- Correlación Mapas > Comparación de pronóstico con pozos cercanos (herramienta Lasso)'),
            html.H6('- Correlación Mapas > Configuración de tiempo al pico de pronósticos'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.3.5', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Declinación manual'),
            html.H6('- Correlación Mapas > Caudal histórico de gas por pozo según selección'),
            html.H6('- Correlación Mapas > Acumulada histórica de gas por pozo según selección'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.3.4', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Configuración de declinación anual de cambio a exponencial (modelo HM)'),
            html.H6('- Pronósticos Petróleo > Configuración de años a pronosticar'),
            html.H6('- Correlación Mapas > Visualización de mapa de sobrepresiones'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.3.3', className = 'card-title')]),
            html.H6('- Correlación Mapas > Pronósticos por correlación para pozos de gas'),
            html.H6('- Correlación Mapas > Selección manual de fluido para correlación a utilizar'),
            html.H6('- Correlación Mapas > Selección automática de fluido para correlación a utilizar'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.3.2', className = 'card-title')]),
            html.H6('- Correlación Mapas > Visualización de mapas de espesor, TOC, Ro y fluido'),
            html.H6('- Correlación Mapas > Visualización de concesiones'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.3.1', className = 'card-title')]),
            html.H6('- Correlación Mapas > Obtención de valores de espesor, TOC y Ro desde mapa'),
            html.H6('- Correlación Mapas > Pronósticos por correlación para pozos de petróleo'),

            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.3.0', className = 'card-title')]),            
            html.H6('- Correlación Mapas > Caudal histórico de petróleo por pozo según selección'),
            html.H6('- Correlación Mapas > Acumulada histórica de petróleo por pozo según selección'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.2.0', className = 'card-title')]),
            html.H6('- Correlación Fracturas > Pronóstico de caudal y acumulada de petróleo según datos de completación'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.1.6', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Filtro de pozos por fecha'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.1.5', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Selección de tiempo de cambio a exponencial (modelo HM)'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.1.4', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Pronóstico automático caudal de petróleo vs tiempo de producción (modelo HM)'),
            html.H6('- Pronósticos Petróleo > Pronóstico automático acumulada de petróleo vs tiempo de producción (modelo HM)'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.1.3', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Tabla de datos históricos + pronósticos exportable a .xlsx'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.1.2', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Acumulada histórica de petróleo vs tiempo de producción'),
            html.H6('- Pronósticos Petróleo > Acumulada con pronóstico automático de petróleo vs tiempo de producción (modelo HYP)'),
            
            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.1.1', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Posibilidad de fijar último caudal en pronóstico automático de petróleo'),

            html.Br(),
            dbc.CardHeader([html.H4('Versión 0.1.0', className = 'card-title')]),
            html.H6('- Pronósticos Petróleo > Caudal histórico de petróleo vs tiempo de producción'),
            html.H6('- Pronósticos Petróleo > Caudal con pronóstico automático de petróleo vs tiempo de producción (modelo HYP)'),
            ],

            id = 'home-changelog-container',
            is_open = False
        ),
    ]),

    common_components.footer],
)


#------------------------------------------------------------------------------
# Callbacks
#------------------------------------------------------------------------------
@app.callback(
    [Output('user_name', 'children'),
    Output('user_name_full', 'children'),
    Output('user_img_small', 'src'),
    Output('user_img_large', 'src')],

    Input('session', 'data'))
def load_user_profile(session):
    '''
    Builds user sidebar profile based on session information.

    Params:
        - session (str): json that stores user current session

    Returns:
        - user_name (str): username from email
        - user_img_small (str): path to user avatar depending on email
    '''
    
    # Retrieve user information from session
    if session and 'LOGGED_IN' in session:
        session_dict = json.loads(session)
        user = session_dict['USER'].split('@')

        if 'vista' in user[1]:
            src = '/assets/vista_logo_masked.png'
        elif 'cgc' in user[1]:
            src = '/assets/cgc_logo_masked.png'
        elif 'fdc' in user[1]:
            src = '/assets/fdc_logo_masked.png'
        elif 'capsa' in user[1]:
            src = '/assets/capsa_logo_masked.png'
        elif 'gmail' in user[1]:
            src = '/assets/gmail_logo_masked.png'
        else:
            src = '/assets/user-avatar_masked.png'

        return user[0], user[0], src, src
    
    else:
        return 'user', 'user', '/assets/user-avatar_masked.png', '/assets/user-avatar_masked.png'


@app.callback(
    [Output('login-msg', 'children'),
    Output('login-toast', 'is_open'),
    Output('session', 'data')],

    Input('login-toast', 'children'),

    State('session', 'data'))
def greet_user(login_children, session):
    '''
    Obtains username (email) from http request header X-MS-CLIENT-PRINCIPAL-NAME
    once logged in, then stores it into session json and shows welcome toast.

    Params:
        - login_children (list): contains children components of toast (not used)
        - session (str | None): json that stores user current session

    Returns:
        - login-msg (str): welcome message to user
        - login-toast-is_open (bool): property of login toast that shows/hides it
        - session (str): json that stores user current session
    '''

    if not session or 'LOGGED_IN' not in session:
        # Retrieve user information from headers
        headers = flask.request.headers
        if 'X-Ms-Client-Principal-Name' in headers:
            USER = headers['X-Ms-Client-Principal-Name']
        else:
            USER = 'user@company.com'

        # Store data in JSON session
        session = {'USER': USER, 'LOGGED_IN': True}

        # Build login msg
        welcome_msg = "Iniciaste sesión como " + USER

        return welcome_msg, True, json.dumps(session)
    else:
        return '', False, session


@app.callback(
    [Output('user-config-toast', 'is_open'),
    Output('header-user-arrow', 'className')],

    [Input('user_img_small', 'n_clicks'),
    Input('header-user-arrow', 'n_clicks'),
    Input('user-config-toast', 'is_open')]
)
def open_user_config(img_click, arrow_click, toast_open):
    '''
    Shows or hides user config toast, controlled by click on user image or its 
    arrow.

    Params:
        - img_click (int): number of clicks on user image
        - arrow_click (int): number of clicks on user image arrow
        - toast_open (bool): indicates whether toast is open
    
    Returns:
        - toast_open (bool): indicates whether toast is open
        - header-user-arrow
    '''

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # If image or arrow clicked, flip toast state and arrow
    if ('img' in trigger_id) or ('arrow' in trigger_id):
        arrow = 'fas fa-chevron-down' if toast_open else 'fas fa-chevron-up'
        return not toast_open, arrow
    else:
        return False, 'fas fa-chevron-down'


@app.callback(
    [Output('home-changelog-container', 'is_open'),
    Output('home-changelog-btn-msg', 'children'),
    Output('home-changelog-btn-arrow', 'className')],

    Input('home-changelog-button', 'n_clicks'),

    State('home-changelog-container', 'is_open')
)
def show_hide_changelog(button_click, container_open):
    '''
    Shows or hides oldest changelog.

    Params:
        - button_click (int | None): number of button clicks
        - container_open (bool): indicates whether to open toast
    
    Returns:
        - container_open (bool): indicates whether to open toast
        - btn_msg (str): button text ('Más' / 'Menos')
        - btn_arrow (str): indicates the arrow className (up or down)
    '''

    if button_click:
        if container_open:
            return False, 'Más', 'fas fa-chevron-down'
        else:
            return True, 'Menos', 'fas fa-chevron-up'
    else:
        return False, 'Más', 'fas fa-chevron-down'