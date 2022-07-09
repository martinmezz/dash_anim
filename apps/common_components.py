import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from core.global_vars import CONFIG


#------------------------------------------------------------------------------
# Header
#------------------------------------------------------------------------------
header = html.Div([
    # FDC logo
    html.Img(id='fdc-logo', src='/assets/fdc-logo.png'),

    # User info
    html.Div([
        html.H6(
            id = 'user_name',
            children = '',
            className = 'header-username',
        ),

        html.Img(
            id = 'user_img_small',
            src = '/assets/user-avatar_masked.png',
        ),

        html.P(
            className = "fas fa-chevron-down",
            id = 'header-user-arrow'
        )],
        id='user_name_and_img'
    )],
    id = 'header',
    className = 'header'
)

#------------------------------------------------------------------------------
# Navbar
#------------------------------------------------------------------------------
navbar = html.Div([
    dbc.Nav([
        # Home
        dbc.NavLink(
            ['Inicio'],
            href = '/',
            active = 'exact'
        ),
        
        # Oil forecasts
        dbc.NavLink(
            ['Pronósticos Petróleo'],
            href = '/oil-forecast',
            active = 'exact'
        ),
        
        # Gas forecasts
        dbc.NavLink(
            ['Pronósticos Gas'],
            href = '/gas-forecast',
            active = 'exact'
        ),
        
        # Maps
        dbc.NavLink(
            ['Correlación Mapas'],
            href = '/maps',
            active = 'exact'
        ),

        # Support
        dbc.NavLink(
            ['Ayuda'],
            href = '/support',
            active = 'exact'
        ),

        # Norby
        dbc.NavLink(
            ['Norby'],
            href = '/norby',
            active = 'exact'
        ),
        ],

        pills = True
    )],

    className = 'ribbon-navbar'
)

#------------------------------------------------------------------------------
# Social media
#------------------------------------------------------------------------------
social_media_buttons = html.Div([
    html.A([
        dbc.Button([
            html.P(className="fab fa-instagram", style={'margin': 0})],
            color = 'primary',
            className = 'social-media-button'
        )],
        href = 'https://www.instagram.com/fdcdeargentina/',
        target = "_blank"
    ),
    
    html.A([
        dbc.Button([
            html.P(className="fab fa-twitter", style={'margin': 0})],
            color = 'primary',
            className = 'social-media-button'
        )],
        href = 'https://twitter.com/FDC_Engineering',
        target = "_blank"
    ),
    
    html.A([
        dbc.Button([
            html.P(className="fab fa-linkedin-in", style={'margin': 0})],
            color = 'primary',
            className = 'social-media-button'
        )],
        href = 'https://ar.linkedin.com/company/field-development-consultants',
        target = "_blank"
    )],

    style = {'paddingTop': '5px', 'textAlign': 'right'}
)

#------------------------------------------------------------------------------
# Footer
#------------------------------------------------------------------------------
footer = dbc.Card([
    html.Div([
        html.H6('2022 FDC de Argentina', className='control-title'),

        html.Div([
            html.H6(['La Paz 1043 (B1640CXE) Martinez, Buenos Aires, Argentina'],
                className='control-title'
            ),

            html.Div(style={'width': '1rem'}),

            html.H6(['+54-11-4718-5707'],
                className='control-title'
            ),

            html.Div(style={'width': '1rem'}),

            html.H6(['info@fdc-group.com'],
                className='control-title'
            ),],

            style = {'display': 'flex'}
        )],
        id = 'footer-text'
    ),

    social_media_buttons],
    id = 'footer'
)

#------------------------------------------------------------------------------
# Logo
#------------------------------------------------------------------------------
logo = html.Div([
    html.A([
        html.Img(
            src = '/assets/fdc-logo.png',
            height = 80,
        )],
        href = 'https://fdc-group.com/',
        target = "_blank"
    )],
    style={'textAlign': 'right', 'padding-right': '8px'}
)

#------------------------------------------------------------------------------
# Toasts
#------------------------------------------------------------------------------
login_toast = dbc.Toast(
    children=[html.P([], id = 'login-msg')],
    id = "login-toast",
    header = "Login",
    icon = "success",
    is_open = False,
    dismissable = True,
    duration = 4000,
    className = 'toast-msg',
)

db_toast = dbc.Toast(
    children=[html.P([], id = 'db-msg')],
    id = "db-toast",
    header = "Exportar a DB",
    icon = "warning",
    is_open = False,
    dismissable = True,
    duration = 4000,
    className = 'toast-msg',
)

user_config_toast = dbc.Toast(
    children = [
        html.P([
            html.Img(
                id = 'user_img_large',
                src = '/assets/user-avatar_masked.png',
                height = 60,
            ),

            html.H6(
                children=[''],
                id = 'user_name_full',
                className = 'header-username',
            )],
            
            id = 'user-config',
            style={'background-color': '#2A5261'}
        ),

        html.Br(),

        dbc.Row([
            dbc.Col([
                html.H6('Idioma', className = 'control-title')],
                className = 'control-div-row'
            ),

            dbc.Col([
                dcc.Dropdown(
                    id = 'user_config_lang',
                    options = [
                        {'label': 'Español', 'value': 'ES'},
                        {'label': 'English <pronto> ', 'value': 'EN', 'disabled': True}
                    ],
                    value = 'ES',
                    multi = False,
                    clearable=False,
                    style = {'width': '100%'}
                )],
                className = 'control-div-row'
            )
        ]),

        dbc.Row([
            dbc.Col([
                html.H6('Unidades', className = 'control-title')],
                className = 'control-div-row'
            ),

            dbc.Col([
                dcc.Dropdown(
                    id = 'user_config_units',
                    options = [
                        {'label': 'Métricas', 'value': 'SI'},
                        {'label': 'Imperiales <pronto> ', 'value': 'IMPERIAL', 'disabled': True}
                    ],
                    value = 'SI',
                    multi = False,
                    clearable=False,
                    style = {'width': '100%'}
                )],
                className = 'control-div-row'
            )
        ]),

        html.Br(),

        html.Br(),

        html.Br(),

        dbc.Row([
            html.A([
                html.Img(src = '/assets/exit.png'), 'Cerrar sesión'],
                href = 'https://fdc-dash.azurewebsites.net/.auth/logout',
                id = "signout-btn",
                className = 'control-btn',
            )],
            className = 'control-div-row'
        )
    ],
    id = "user-config-toast",
    header = None,
    icon = None,
    is_open = False,
    dismissable = True,
    duration = None,
)