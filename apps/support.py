from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from apps import common_components
from app import app
from core import issue_tracking as its
import json
from core.global_vars import CONFIG


#------------------------------------------------------------------------------
# Ribbon
#------------------------------------------------------------------------------
ribbon = html.Div()

#------------------------------------------------------------------------------
# Layout
#------------------------------------------------------------------------------
layout = html.Div([

    html.Div([
        # Comments card
        dbc.Card([
            dbc.CardHeader([
                html.H4('Escribí tu comentario acá',
                    className = 'card-title'
                )]
            ),

            dcc.Textarea(
                id = 'textarea',
                value = '',
                style = {'width': '100%', 'height': '300px'},
            ),

            html.Br(),

            html.H6(
                'En caso de reportar un error/bug por favor describí la serie de pasos necesarios para reproducirlo.',
            ),

            html.Br(),

            html.Div([
                dcc.Loading([
                    html.Button(
                        'Enviar',
                        id = 'submit-comment',
                        className = 'control-btn',
                    ),],
                    type = 'dot',
                    color = '#2A5261',
                    fullscreen = False,
                )],
                style = {
                    'width': '100%',
                    'display': 'flex',
                    'justify-content': 'center',
                    'margin-bottom': '5px',
                }
            )],
            style = {'width': '60%',}
        ),

        dbc.Toast(
            children=[html.P("Gracias por enviar tus comentarios.",
                    className = "mb-0")],
            id = "submit-toast",
            header = "Comentario enviado",
            icon = "primary",
            is_open = False,
            dismissable = True,
            duration = 4000,
            style={
                "position": "fixed",
                "bottom": 5,
                "right": 10,
                "width": 350
            }
        ),
        
        # dbc.Row([
        #     dbc.Col([
        #         html.H5('Próximamente podrás incluir un archivo o captura de pantalla en el siguiente espacio:'),

        #         dcc.Upload(
        #             id='upload-files',
        #             children = html.Div([
        #                 '<PROXIMAMENTE> Arrastrá los archivos acá o ',
        #                 html.A('hacé click para seleccionarlos (Max 10 MB)')
        #             ]),
        #             max_size = (10_000_000),
        #             style={
        #                 'width': '100%',
        #                 'height': '90px',
        #                 'lineHeight': '80px',
        #                 'borderWidth': '2px',
        #                 'borderStyle': 'dashed',
        #                 'borderRadius': '5px',
        #                 'textAlign': 'center',
        #                 'margin': '0px'
        #             },
        #             # Allow multiple files to be uploaded
        #             multiple=True
        #         )],
        #         style = {'paddingLeft': '15px'}
        #     )
        # ]),

        html.Div([
            common_components.footer,],
        )],

        style = {
            'height': '92vh',
            'display': 'flex',
            'flex-direction': 'column',
            'justify-content': 'space-between'
        }
    )
])


#------------------------------------------------------------------------------
# Callbacks
#------------------------------------------------------------------------------
@app.callback(
    [Output('submit-toast', 'is_open'),
    Output('textarea', 'value'),
    Output('submit-comment', 'style')],

    Input('submit-comment', 'n_clicks'),

    [State('textarea', 'value'),
    State('session', 'data')]
)
def submit_comment(submit_click, comments, session):
    '''
    TODO: completar docstring
    '''
    if submit_click:
        if session and 'LOGGED_IN' in session:
            session_dict = json.loads(session)
            comments += '\n'.join(('\nfdc-dash ' + CONFIG['VERSION'],
                session_dict['USER']))

        its.new_issue(comments)
        return True, 'Gracias por tus comentarios.', {'display': 'none'}
    
    return False, '', {'display': 'block'}