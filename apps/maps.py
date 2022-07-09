import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from plotly.graph_objects import Layout
import dash_table as dt
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from app import app
from apps import common_components
import dash_daq as daq
from core import map_correlation as mcorr
from core import decline_curve_analysis as dca
from core import database as db
from datetime import datetime, date
import json
from dash.dash import no_update


#------------------------------------------------------------------------------
# Ribbon
#------------------------------------------------------------------------------
ribbon = html.Div([
    # Wells info button
    html.Button([
        html.Img(
            src = '/assets/btn-info.png',
            className = 'ribbon-icon',
        ),
        html.P('Info de pozos')],
        id = 'maps-wells-info-button',
        className = 'ribbon-btn',
    ),
    
    # Export to DB button
    html.Button([
        html.Img(
            src = '/assets/db-up.png',
            className = 'ribbon-icon'
        ),
        html.P('Exportar a DB')],
        className = 'ribbon-btn',
        id = 'maps-forecasts-to-db',
    ),
    
    # Export to Excel button
    html.Button([
        html.Img(
            src = '/assets/excel.png',
            className = 'ribbon-icon'
        ),
        html.P('Exportar a Excel')],
        className = 'ribbon-btn',
        id = 'maps-export-table-xls',
        **{'data-dummy': ''}
    ),],
    id = 'maps-ribbon'
)

#------------------------------------------------------------------------------
# Import, clean data, and intial config
#------------------------------------------------------------------------------
# Read static data for all wells
wells_props = db.get_wells_props()
wells_props.dropna(subset=['Pozo_Form', 'Coordenadax', 'Coordenaday'], inplace=True)
wells_props.sort_values(by=['Rama', 'Fracturas'], ascending=True,
    na_position='first', inplace=True)
wells_props.drop_duplicates(subset=['Pozo_Form'], keep='last', inplace=True)

# Read grid and filter points with missing data
df_grid = pd.read_csv('data/grid.csv', sep=';').dropna()

mapbox_acces_token = 'pk.eyJ1IjoibWFudWVscmZkYyIsImEiOiJja2Vzemo2dDIxaGFzMnJvZmkxN3ZlejBvIn0.4T3OGB8KEHWSsFqatVqKMw'


#------------------------------------------------------------------------------
# Layout
#------------------------------------------------------------------------------
layout = html.Div([
    # Stores the filtered dataset
    dcc.Store(id='maps-filtered-data', storage_type='memory'),

    # Store user forecasts
    dcc.Store(id='maps-forecasts', storage_type='memory'),

    # Store user current dropdown selection
    dcc.Store(id='maps-user-selection', storage_type='memory'),

    #----------------------------------------
    # Filter sidebars
    #----------------------------------------
    # Expanded sidebar
    html.Div([
        html.Button([
            html.Img(
                src = 'assets/arrow-from-right.png',
                className='sidebar-collapse-icon'
            )],
            id = 'maps-filter-sidebar-collapse-btn',
            className = 'left-sidebar-collapse-btn',
        ),

        html.Br(),

        # Sidebar title
        html.H5('Selección de pozos', className = 'sidebar-main-title'),

        # Dates filter
        html.H6('Fecha inicio producción', className = 'sidebar-filter-title'),

        html.Div([
            # Date picker
            dcc.DatePickerRange(
                id = 'maps-date-picker',
                calendar_orientation = 'horizontal',
                start_date_placeholder_text = "Desde",
                display_format = 'DD-MM-YYYY',
                first_day_of_week = 1,
                end_date_placeholder_text = "Hasta"
            ),

            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "maps-datepicker-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        # Geometry filter
        html.H6('Geometría', className = 'sidebar-filter-title'),

        html.Div([
            # Geometry dropdown
            dbc.DropdownMenu(
                label = '0 seleccionados',
                children = [
                    dcc.Checklist(
                        id = 'maps-geometry-dropdown',
                        value = [],
                        options = [],
                        labelClassName = 'checklist-label',
                        inputClassName = 'checklist-checkbox',
                        className = 'sidebar-checklist'
                    )
                ],
                id = 'maps-geometry-container',
                toggleClassName = 'dropdown-btn'
            ),
            
            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "maps-geometry-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        # Fluid filter
        html.H6('Fluido', className = 'sidebar-filter-title'),

        html.Div([
            # Formation dropdown
            dbc.DropdownMenu(
                label = '0 seleccionados',
                children = [
                    dcc.Checklist(
                        id = 'maps-fluid-dropdown',
                        value = [],
                        options = [],
                        labelClassName = 'checklist-label',
                        inputClassName = 'checklist-checkbox',
                        className = 'sidebar-checklist'
                    )
                ],
                id = 'maps-fluid-container',
                toggleClassName = 'dropdown-btn'
            ),

            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "maps-fluid-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        # Company and field filter
        html.H6('Empresa y yacimiento', className = 'sidebar-filter-title'),

        html.Div([
            # Field dropdown
            dbc.DropdownMenu(
                label = '0 seleccionados',
                children = [
                    dcc.Checklist(
                        id = 'maps-field-dropdown',
                        value = [],
                        options = [],
                        labelClassName = 'checklist-label',
                        inputClassName = 'checklist-checkbox',
                        className = 'sidebar-checklist'
                    )
                ],
                id = 'maps-field-container',
                toggleClassName = 'dropdown-btn'
            ),
            
            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "maps-field-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        # Lateral length filter
        html.H6('Rama', className = 'sidebar-filter-title'),

        html.Div([
            # Lateral length inputs and slider
            dcc.Input(
                id = 'maps-latlength-input-start',
                type = 'number',
                placeholder = 'Min',
                debounce = True,
                className = 'input-latlen'
            ),

            dcc.Input(
                id = 'maps-latlength-input-end',
                type = 'number',
                placeholder = 'Max',
                debounce = True,
                className = 'input-latlen'
            ),
            
            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "maps-latlength-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        dcc.RangeSlider(id = 'maps-latlength-slider'),

        # Fracture stages filter
        html.H6('Fracturas', className = 'sidebar-filter-title'),

        html.Div([
            # Fractures inputs and slider
            dcc.Input(
                id = 'maps-fracs-input-start',
                type = 'number',
                placeholder = 'Min',
                debounce = True,
                className = 'input-latlen'
            ),

            dcc.Input(
                id = 'maps-fracs-input-end',
                type = 'number',
                placeholder = 'Max',
                debounce = True,
                className = 'input-latlen'
            ),

            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "maps-fracs-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        dcc.RangeSlider(id = 'maps-fracs-slider'),

        # Wellname filter
        html.Div([
            html.H6('Nombre de pozo', className = 'sidebar-filter-title'),

            # html.Img(
            #     src = 'assets/exclamation.png',
            #     id = 'maps-select-all-warning',
            #     className = 'select-all-warning',
            # ),

            # dbc.Tooltip(
            #     'Se ocultó "Seleccionar todos" porque hay más de 250 pozos disponibles',
            #     target = "maps-select-all-warning",
            # )
            ],

            className = 'filter-row'
        ),

        html.Div([
            # Wells dropdown
            dcc.Loading(
                children = [
                    dbc.DropdownMenu(
                        label = '0 seleccionados',
                        children = [
                            dcc.Checklist(
                                id = 'maps-wells-dropdown',
                                value = [],
                                options = [],
                                labelClassName = 'checklist-label',
                                inputClassName = 'checklist-checkbox',
                                className = 'sidebar-checklist'
                            )
                        ],
                        id = 'maps-wells-container',
                        toggleClassName = 'dropdown-btn'
                    ),

                    # Clear button
                    html.Button(
                        html.Img(
                            src='assets/x.png',
                            className='sidebar-clear-icon'
                        ),
                        id = "maps-wells-clear",
                        className = 'sidebar-clear-btn',
                        n_clicks = 0
                    )
                ],
                type = 'dot',
                color = '#2A5261',
                fullscreen = False,
                parent_className = 'filter-row'
            )],

            className = 'filter-row'
        )],
        id = 'maps-filter-sidebar-expanded',
        className = 'show-filter-sidebar-expanded'
    ),

    # Collapsed sidebar
    html.Div([
        html.Button([
            html.Img(
                src = 'assets/filter.png',
                className='sidebar-expand-icon'
            )],
            id = 'maps-filter-sidebar-expand-btn',
            className = 'sidebar-expand-btn'
        )
        ],
        id = 'maps-filter-sidebar-collapsed',
        className = 'hide-element'
    ),

    #----------------------------------------
    # Main content
    #----------------------------------------
    dbc.Container([
        #----------------------------------------
        # Wells info table
        #----------------------------------------
        dbc.Collapse([
            dbc.Card([
                dbc.CardHeader([
                    html.H4(
                        'Información de pozos seleccionados',
                        className = 'card-title'
                    )]
                ),

                dt.DataTable(
                id = 'maps-wells-info-table',
                columns = [
                    {'name': 'Pozo:Form', 'id': 'Pozo_Form_P'},
                    {'name': 'MinFecha', 'id': 'MinFecha'},
                    {'name': 'Np [m3]', 'id': 'Np'},
                    {'name': 'Gp [Mm3]', 'id': 'Gp'},
                    {'name': 'Fracturas', 'id': 'Fracturas'},
                    {'name': 'Rama [m]', 'id': 'Rama'},
                    {'name': 'qo_ef_peak [m3/d]', 'id': 'qo_ef_peak'},
                    {'name': 'qg_ef_peak [Mm3/d]', 'id': 'qg_ef_peak'},
                    {'name': 'qo_avg [m3/d]', 'id': 'qo_avg'},
                    {'name': 'qg_avg [Mm3/d]', 'id': 'qg_avg'}
                ],
                style_header = {'fontWeight': 'bold'},
                filter_action = 'native',
                page_size = 10
                )]
            )],
            id = 'maps-wells-info-container',
            is_open = False
        ),

        #----------------------------------------
        # Correlation forecasts
        #----------------------------------------
        dbc.Card([
            dbc.CardHeader([
                html.H4(
                    'Pronósticos por correlación',
                    className = 'card-title'
                )]
            ),

            dbc.Row([
                # Fluid selection column
                dbc.Col([
                    html.H6(
                        'Correlación de fluido',
                        className = 'control-title'
                    ),
                    
                    dcc.Dropdown(
                        id = 'corr_selected',
                        options = [
                            {'label': 'Selección automática de fluido', 'value': 'AUTO'},
                            {'label': 'Correlación de petróleo', 'value': 'OIL'},
                            {'label': 'Correlación de gas', 'value': 'GAS'},
                        ],
                        multi = False,
                        value = 'AUTO',
                        clearable = False,
                        searchable = False,
                        className = 'dropdown-control-wide',
                    )],
                    className = 'control-div',
                    xs = {'size': 12, 'order': 1},
                    sm = {'size': 12, 'order': 1},
                    md = {'size': 6, 'order': 1},
                    lg = {'size': 6, 'order': 1},
                    xl = {'size': 6, 'order': 1},
                ),
            ]),

            dbc.Row([
                # Forecasts name column
                dbc.Col([
                    html.H6(
                        'Nombre del pronóstico',
                        className = 'control-title'
                    ),
                    
                    dcc.Input(
                        id = 'maps-synth-wellname',
                        type = 'text',
                        debounce = True,
                        pattern = '[^_ \s]+',
                        className = 'control-input-wide'
                    )],
                    className = 'control-div',
                    xs = {'size': 12, 'order': 1},
                    sm = {'size': 12, 'order': 1},
                    md = {'size': 5, 'order': 1},
                    lg = {'size': 5, 'order': 1},
                    xl = {'size': 3, 'order': 1},
                ),

                # Forecasts date column
                dbc.Col([
                    html.H6(
                        'Fecha inicio pronóstico',
                        className = 'control-title'
                    ),

                    dcc.DatePickerSingle(
                        id = 'maps-synth-date-picker',
                        calendar_orientation = 'horizontal',
                        display_format = 'DD-MMM-YYYY',
                        first_day_of_week = 1,
                        date = date.today(),
                        className = 'control-input-datepicker',
                    )],
                    className = 'control-div',
                    xs = {'size': 12, 'order': 2},
                    sm = {'size': 12, 'order': 2},
                    md = {'size': 5, 'order': 2},
                    lg = {'size': 4, 'order': 2},
                    xl = {'size': 3, 'order': 2},
                )
            ]),

            dbc.Row([
                # Lateral length column
                dbc.Col([
                    html.H6('Rama [m]', className = 'control-title'),

                    dcc.Input(
                        id = 'rama',
                        type = 'number',
                        placeholder = 'm',
                        value = 2500,
                        debounce = True,
                        min = 0,
                        max = 9000,
                        className = 'control-input',
                    ),],
                    className = 'control-div',
                    xs = {'size': 6, 'order': 1},
                    sm = {'size': 6, 'order': 1},
                    md = {'size': 5, 'order': 1},
                    lg = {'size': 3, 'order': 1},
                    xl = {'size': 1, 'order': 1},
                ),

                # Frac stages column
                dbc.Col([
                    html.H6('Fracturas', className = 'control-title'),

                    dcc.Input(
                        id = 'fracturas',
                        type = 'number',
                        value = 35,
                        debounce = True,
                        min = 20,
                        max = 500,
                        className = 'control-input',
                    )],
                    className = 'control-div',
                    xs = {'size': 6, 'order': 2},
                    sm = {'size': 6, 'order': 2},
                    md = {'size': 5, 'order': 2},
                    lg = {'size': 3, 'order': 2},
                    xl = {'size': 1, 'order': 2},
                ),

                # Peak time column
                dbc.Col([
                    html.H6('Tiempo al pico [d]', className = 'control-title'),

                    dcc.Input(
                        id = 't_peak',
                        type = 'number',
                        value = 90,
                        debounce = True,
                        min = 0,
                        max = 360,
                        className = 'control-input',
                    )],
                    className = 'control-div',
                    xs = {'size': 6, 'order': 3},
                    sm = {'size': 6, 'order': 3},
                    md = {'size': 5, 'order': 3},
                    lg = {'size': 3, 'order': 3},
                    xl = {'size': 2, 'order': 3},
                ),

                # Thickness column
                dbc.Col([
                    html.H6('Espesor [m]', className = 'control-title'),

                    dcc.Input(
                        id = 'thickness',
                        type = 'number',
                        value = 90,
                        debounce = True,
                        min = 0,
                        max = 2000,
                        className = 'control-input',
                    )],
                    className = 'control-div',
                    xs = {'size': 6, 'order': 4},
                    sm = {'size': 6, 'order': 4},
                    md = {'size': 5, 'order': 4},
                    lg = {'size': 3, 'order': 4},
                    xl = {'size': 1, 'order': 4},
                ),

                # TOC column
                dbc.Col([
                    html.H6('TOC', className = 'control-title'),

                    dcc.Input(
                        id = 'toc',
                        type = 'number',
                        debounce = True,
                        min = 0,
                        max = 99,
                        className = 'control-input',
                    )],
                    className = 'control-div',
                    xs = {'size': 6, 'order': 5},
                    sm = {'size': 6, 'order': 5},
                    md = {'size': 5, 'order': 5},
                    lg = {'size': 3, 'order': 5},
                    xl = {'size': 1, 'order': 5},
                ),

                # Ro column
                dbc.Col([
                    html.H6('Ro', className = 'control-title'),

                    dcc.Input(
                        id = 'ro',
                        type = 'number',
                        debounce = True,
                        min = 0,
                        max = 100,
                        className = 'control-input',
                    )],
                    className = 'control-div',
                    xs = {'size': 6, 'order': 6},
                    sm = {'size': 6, 'order': 6},
                    md = {'size': 5, 'order': 6},
                    lg = {'size': 3, 'order': 6},
                    xl = {'size': 2, 'order': 6},
                ),

                # Uncertainty column
                dbc.Col([
                    html.H6('Incertidumbre [%]', className = 'control-title'),

                    dcc.Input(
                        id = 'map_corr_uncertainty',
                        type = 'number',
                        debounce = True,
                        min = 0,
                        max = 99,
                        value = 30,
                        className = 'control-input',
                    )],
                    className = 'control-div',
                    xs = {'size': 6, 'order': 7},
                    sm = {'size': 6, 'order': 7},
                    md = {'size': 5, 'order': 7},
                    lg = {'size': 3, 'order': 7},
                    xl = {'size': 2, 'order': 7},
                ),

                # Target column
                dbc.Col([
                    html.H6('Target', className = 'control-title'),

                    dcc.Dropdown(
                        id = 'target_depth',
                        options = [
                            {'label': 'Promedio', 'value': 0},
                            {'label': 'Cocina', 'value': 1},
                            {'label': 'Orgánico', 'value': 2},
                        ],
                        multi = False,
                        value = 0,
                        clearable = False,
                        searchable = False,
                        className = 'dropdown-control',
                    )],
                    className = 'control-div',
                    xs = {'size': 6, 'order': 8},
                    sm = {'size': 6, 'order': 8},
                    md = {'size': 5, 'order': 8},
                    lg = {'size': 3, 'order': 8},
                    xl = {'size': 2, 'order': 8},
                ),
            ])
        ]),

        #----------------------------------------
        # Map and plots
        #----------------------------------------
        dbc.Row([
            # Map card
            dbc.Col([
                dbc.Card([
                    dbc.Row([
                        dbc.Col([
                            html.H6('Tipo de mapa', className = 'control-title'),
                        
                            dcc.Dropdown(
                                id = 'map_type',
                                options = [
                                    {'label': 'Mapa base', 'value': 'BASE'},
                                    {'label': 'TOC', 'value': 'TOC'},
                                    {'label': 'Espesor', 'value': 'THICKNESS'},
                                    {'label': 'Ro', 'value': 'RO'},
                                    {'label': 'Fluido', 'value': 'FLUID'},
                                    {'label': 'Sobrepresión', 'value': 'OVERPRESSURE'}
                                ],
                                value = 'BASE',
                                multi = False,
                                clearable = False,
                                searchable = False,
                                className = 'dropdown-control',
                            )],
                            className = 'control-div',
                            xs = {'size': 12, 'order': 1},
                            sm = {'size': 12, 'order': 1},
                            md = {'size': 6, 'order': 1},
                            lg = {'size': 7, 'order': 1},
                            xl = {'size': 6, 'order': 1},
                        ),
                        
                        dbc.Col([
                            html.Div([
                                daq.ToggleSwitch(
                                    id = 'maps-overlap-wells',
                                    size = 35,
                                    value = False,
                                    className = 'toggle-switch',
                                ),

                                html.H6(
                                    'Mostrar pozos',
                                    className = 'control-title',
                                ),],
                                className = 'no-padding-display-flex',
                            ),],
                            className = 'control-div',
                            xs = {'size': 10, 'order': 2},
                            sm = {'size': 10, 'order': 2},
                            md = {'size': 5, 'order': 2},
                            lg = {'size': 4, 'order': 2},
                            xl = {'size': 4, 'order': 2},
                        ),
                        
                        dbc.Col([
                            html.Div([
                                html.Img(
                                    id = 'map-tooltip',
                                    src = '/assets/question.png',
                                    className = 'control-icon',
                                ),
                                    
                                dbc.Tooltip(
                                    "Para comparar un pronóstico con pozos cercanos usá la herramienta Lasso del mapa",
                                    target = "map-tooltip",
                                )],
                                className = 'no-padding-display-flex-end',
                            )],
                            className = 'control-div',
                            xs = {'size': 2, 'order': 3},
                            sm = {'size': 2, 'order': 3},
                            md = {'size': 1, 'order': 3},
                            lg = {'size': 1, 'order': 3},
                            xl = {'size': 2, 'order': 3},
                        )]
                    ),
                    
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id = 'map',
                                style = {"height": 780},
                                config={
                                    'modeBarButtonsToRemove': ['select2d']
                                }
                            )],
                            className = 'control-div',
                        )
                    ])],

                    className = 'maps-main-card',
                )],

                className = 'control-div',
                lg = {'size': 6, 'order': 1},
                xl = {'size': 5, 'order': 1},
            ),

            # Plots card
            dbc.Col([
                dbc.Card([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                daq.ToggleSwitch(
                                    id = 'maps-frac-normalize',
                                    size = 35,
                                    value = False,
                                    className = 'toggle-switch',
                                ),

                                html.H6(
                                    'Normalizar por etapas de fractura',
                                    className = 'control-title',
                                ),],
                                className = 'toggle-scale'
                            )],

                            className = 'control-div-row'
                        ),
                        
                        dbc.Col([
                            html.Div([
                                html.H6('Lineal', className = 'control-title'),

                                daq.ToggleSwitch(
                                    id = 'maps-log-scale',
                                    size = 35,
                                    value = True,
                                    className = 'toggle-switch',
                                ),

                                html.H6('Log', className = 'control-title'),],
                                className = 'toggle-scale'
                            ),
                            
                            html.Button(
                                'Reset plot',
                                id = 'reset_plot',
                                className = 'control-btn',
                            )],

                            className = 'control-div-row-flex-end'
                        )],

                        className = 'maps-plots-ctrls',
                    ),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Tabs([
                                dbc.Tab([
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Loading(
                                                children = [
                                                    dcc.Graph(
                                                        id = 'oil_rates',
                                                        )
                                                ],
                                                type = 'dot',
                                                color = '#2A5261',
                                                fullscreen = False
                                            )],
                                            className = 'control-div',
                                        )
                                    ]),

                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Loading(
                                                children = [
                                                    dcc.Graph(
                                                        id = 'oil_cumulatives',
                                                        
                                                    )
                                                ],
                                                type = 'dot',
                                                color = '#2A5261',
                                                fullscreen = False
                                            )],
                                            className = 'control-div',
                                        )]
                                    )],

                                    label = "Petróleo"
                                ),
                                
                                dbc.Tab([
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Loading(
                                                children = [
                                                    dcc.Graph(
                                                        id = 'gas_rates',
                                                        )
                                                ],
                                                type = 'dot',
                                                color = '#2A5261',
                                                fullscreen = False
                                            )],
                                            className = 'control-div',
                                        )
                                    ]),

                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Loading(
                                                children = [
                                                    dcc.Graph(
                                                        id = 'gas_cumulatives',
                                                        
                                                    )
                                                ],
                                                type = 'dot',
                                                color = '#2A5261',
                                                fullscreen = False
                                            )],
                                            className = 'control-div',
                                        )]
                                    )],

                                    label = "Gas"
                                ),
                                
                                dbc.Tab([
                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Loading(
                                                children = [
                                                    dcc.Graph(
                                                        id = 'water_rates',
                                                        )
                                                ],
                                                type = 'dot',
                                                color = '#2A5261',
                                                fullscreen = False
                                            )],
                                            className = 'control-div',
                                        )
                                    ]),

                                    dbc.Row([
                                        dbc.Col([
                                            dcc.Loading(
                                                children = [
                                                    dcc.Graph(
                                                        id = 'water_cumulatives',
                                                        
                                                    )
                                                ],
                                                type = 'dot',
                                                color = '#2A5261',
                                                fullscreen = False
                                            )],
                                            className = 'control-div',
                                        )]
                                    )],

                                    label = "Agua"
                                ),]
                            )],

                            className = 'control-div',
                        )
                    ])],

                    className = 'maps-main-card',
                )],

                className = 'control-div',
                lg = {'size': 6, 'order': 1},
                xl = {'size': 7, 'order': 2},
            ),
        ]),

        #----------------------------------------
        # DataTable row
        #----------------------------------------
        dbc.Card([
            dbc.CardHeader([
                html.H4(
                    'Pronósticos',
                    className = 'card-title'
                )]
            ),

            # DataTable with forecast
            dt.DataTable(
                id = 'maps-history-forecasts-table',
                columns = [
                    {'name': 'Pronostico', 'id': 'FORECAST'},
                    {'name': 'TdP [d]', 'id': 'TdP'},
                    {'name': 'qo [m3/d]', 'id': 'qo'},
                    {'name': 'Np [m3]', 'id': 'Np'},
                    {'name': 'GOR [m3/m3]', 'id': 'GOR'},
                    {'name': 'qg [Mm3/d]', 'id': 'qg'},
                    {'name': 'Gp [Mm3]', 'id': 'Gp'},
                ],
                style_header={'fontWeight': 'bold'},
                filter_action = 'native',
                page_size = 15,
                export_format = 'xlsx'
            ),
        ]),

        common_components.footer,

        dbc.Toast([
            html.P("Los valores seleccionados se encuentran fuera del rango recomendado para la correlación PETROLEO:",
                className = "mb-0"),
            html.P("3.75 < TOC < 5", className = "mb-0"),
            html.P("0.9 < Ro < 1.3", className = "mb-0"),
            html.P("100 < Espesor < 220", className = "mb-0"),
            html.P("20 < Fracturas < 60", className = "mb-0")
        ],
        id = "corr-toast-oil",
        header = "Atención!",
        icon = "primary",
        dismissable = True,
        duration = 6000,
        is_open = False,
        style = {"position": "fixed", "bottom": 5, "right": 10, "width": 350}
    ),

    dbc.Toast([
            html.P("Los valores seleccionados se encuentran fuera del rango recomendado para la correlación GAS:",
                className = "mb-0"),
            html.P("3.75 < TOC < 5.75", className = "mb-0"),
            html.P("1.4 < Ro < 1.6", className = "mb-0"),
            html.P("150 < Espesor < 280", className = "mb-0"),
            html.P("10 < Fracturas < 60", className = "mb-0")
        ],
        id = "corr-toast-gas",
        header = "Atención!",
        icon = "primary",
        dismissable = True,
        duration = 6000,
        is_open = False,
        style = {"position": "fixed", "bottom": 5, "right": 10, "width": 350}
    )
    ],
    
    id = 'maps-container',
    className = 'left-expanded',
    fluid = True
    ),
])


#------------------------------------------------------------------------------
# Callbacks
#------------------------------------------------------------------------------
@app.callback(
    [Output('maps-geometry-dropdown', 'options'),
    Output('maps-geometry-dropdown', 'value'),
    Output('maps-fluid-dropdown', 'options'),
    Output('maps-fluid-dropdown', 'value'),
    Output('maps-field-dropdown', 'options'),
    Output('maps-field-dropdown', 'value'),
    Output('maps-wells-dropdown', 'options'),
    Output('maps-user-selection', 'data'),
    Output('maps-latlength-input-start', 'min'),
    Output('maps-latlength-input-start', 'max'),
    Output('maps-latlength-input-end', 'min'),
    Output('maps-latlength-input-end', 'max'),
    Output('maps-latlength-slider', 'min'),
    Output('maps-latlength-slider', 'max'),
    Output('maps-fracs-input-start', 'min'),
    Output('maps-fracs-input-start', 'max'),
    Output('maps-fracs-input-end', 'min'),
    Output('maps-fracs-input-end', 'max'),
    Output('maps-fracs-slider', 'min'),
    Output('maps-fracs-slider', 'max')],

    [Input('maps-date-picker', 'start_date'),
    Input('maps-date-picker', 'end_date'),
    Input('maps-geometry-dropdown', 'value'),
    Input('maps-geometry-clear', 'n_clicks'),
    Input('maps-fluid-dropdown', 'value'),
    Input('maps-fluid-clear', 'n_clicks'),
    Input('maps-field-dropdown', 'value'),
    Input('maps-field-clear', 'n_clicks'),
    Input('maps-latlength-input-start', 'value'),
    Input('maps-latlength-input-end', 'value'),
    Input('maps-fracs-input-start', 'value'),
    Input('maps-fracs-input-end', 'value')],

    State('maps-user-selection', 'data')
)
def update_dropdowns(start_date, end_date, geometry, geom_clear, fluid,
    fluid_clear, field, field_clear, latlen_start, latlen_end, fracs_start,
    fracs_end, previous):
    '''
    Updates select wells dropdown based on date picker, geometry, fluid,
    company/field and lateral length selection.

    TODO: COMPLETAR DOCSTRING

    Params:
        start_date (str | None): formated as YYYY-MM-DD
        end_date (str | None): formated as YYYY-MM-DD
        geometry
        fluid
        field
        previous

    Returns:
        geometry_dropdown
        fluid_dropdown
        field_dropdown
        wellnames_dropdown (list of dict): contains wellnames for dropdown
        user_selection
    '''

    #----------------------------------------
    # Clear dropdowns if button clicked
    #----------------------------------------
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if geom_clear and 'geometry-clear' in trigger_id: geometry = []
    if fluid_clear and 'fluid-clear' in trigger_id: fluid = []
    if field_clear and 'field-clear' in trigger_id: field = []

    #----------------------------------------
    # Get dataset from DB
    #----------------------------------------
    dataset = db.filter_wellnames(well_type=None, start_date=start_date,
        end_date=end_date)
    mask_well = dataset['Pozo_Form'].notna()
    
    #----------------------------------------
    # Get user previous selection and assert new selection
    #----------------------------------------
    if previous:
        previous = json.loads(previous)

        # Assert geometry
        if 'ALL' in geometry and ('V' in geometry or 'H' in geometry):
            if 'ALL' in previous['geometry']:
                # ALL must be removed
                geometry.remove('ALL')
            else:
                # Only keep ALL
                for g in geometry: geometry.remove(g)
                geometry.append('ALL')

        # Assert fluid
        if 'ALL' in fluid and len(fluid) > 1:
            if 'ALL' in previous['fluid']:
                # ALL must be removed
                fluid.remove('ALL')
            else:
                # Only keep ALL
                for f in fluid: fluid.remove(f)
                fluid.append('ALL')
            
        # Assert field
        if 'ALL' in field and len(field) > 1:
            if 'ALL' in previous['field']:
                # ALL must be removed
                field.remove('ALL')
            else:
                # Only keep ALL
                for f in field: field.remove(f)
                field.append('ALL')

    #----------------------------------------
    # Filter by geometry
    #----------------------------------------
    if (not geometry
        or ('H' in geometry and 'V' in geometry)
        or 'ALL' in geometry):
        # None, ALL or both selected, do not filter
        mask_geom = dataset['Pozo_Form'].notna()
    elif 'H' in geometry:
        # Keep only horizontal wells
        mask_geom = dataset['Rama'] > 0
    elif 'V' in geometry:
        # Keep only vertical wells
        mask_geom = np.logical_or(dataset['Rama'].isna(), dataset['Rama'] == 0)

    #----------------------------------------
    # Filter by formation (this page only uses VMUT)
    #----------------------------------------
    mask_form = dataset['Pozo_Form'].str.contains('VMUT')

    #----------------------------------------
    # Filter by fluid
    #----------------------------------------
    if (not fluid
        or 'ALL' in fluid):
        # None or ALL selected, do not filter
        mask_fluid = dataset['Pozo_Form'].notna()
    else:
        # Keep only selected fluids
        mask_fluid = ~dataset['Pozo_Form'].notna()
        for f in fluid:
            mask_fluid = np.logical_or(mask_fluid, dataset['Fluido_gor'] == f)
    
    #----------------------------------------
    # Filter by field
    #----------------------------------------
    if (not field
        or 'ALL' in field):
        # None or ALL selected, do not filter
        mask_field = dataset['Pozo_Form'].notna()
    else:
        # Keep only selected fields
        mask_field = ~dataset['Pozo_Form'].notna()
        for f in field:
            mask_field = np.logical_or(mask_field,
                (dataset['Empresa'] + ' > ' + dataset['Yacimiento']) == f)

    #----------------------------------------
    # Filter by lateral length
    #----------------------------------------
    if (latlen_start is None) or (latlen_end is None):
        # None selected, do not filter
        mask_latlen = dataset['Pozo_Form'].notna()
    else:
        # Keep only between selected values
        mask_latlen = np.logical_and(dataset['Rama'] >= latlen_start,
            dataset['Rama'] <= latlen_end)
        
        if not latlen_start: # Take NaNs lateral length as zero
            mask_latlen = np.logical_or(mask_latlen, dataset['Rama'].isna())

    #----------------------------------------
    # Filter by fracs
    #----------------------------------------
    if (fracs_start is None) or (fracs_end is None):
        # None selected, do not filter
        mask_fracs = dataset['Pozo_Form'].notna()
    else:
        # Keep only between selected values
        mask_fracs = np.logical_and(dataset['Fracturas'] >= fracs_start,
            dataset['Fracturas'] <= fracs_end)
        
        if not fracs_start: # Take NaNs fracs as zero
            mask_fracs = np.logical_or(mask_fracs, dataset['Fracturas'].isna())

    #----------------------------------------
    # Update geometry dropdown
    #----------------------------------------
    geometry_dropdown = []
    
    # Wells without lateral length (Vertical)
    if np.logical_or(
        dataset[mask_well & mask_form & mask_fluid & mask_field & mask_latlen
            & mask_fracs]['Rama'].isna(),
        dataset[mask_well & mask_form & mask_fluid & mask_field & mask_latlen
            & mask_fracs]['Rama'] == 0).any():
        if 'ALL' in geometry:
            geometry_dropdown.append({
                'label': 'Vertical',
                'value': 'V',
                'disabled': True
            })
        else:
            geometry_dropdown.append({'label': 'Vertical', 'value': 'V'})

    # Wells with lateral length (Horizontal)
    if (dataset[mask_well & mask_form & mask_fluid & mask_field & mask_latlen
        & mask_fracs]['Rama'] > 0).any():
        if 'ALL' in geometry:
            geometry_dropdown.append({
                'label': 'Horizontal',
                'value': 'H',
                'disabled': True
            })
        else:
            geometry_dropdown.append({'label': 'Horizontal', 'value': 'H'})
    
    # Append 'select all' option
    if geometry_dropdown:
        geometry_dropdown.insert(0, {'label': 'Seleccionar todos', 'value': 'ALL'})

    #----------------------------------------
    # Update fluid dropdown
    #----------------------------------------
    if 'ALL' in fluid:
        fluid_dropdown = [{'label': f, 'value': f, 'disabled': True}
            for f in np.sort(dataset[mask_well & mask_geom & mask_form
            & mask_field & mask_latlen & mask_fracs]['Fluido_gor'].unique())]
    else:
        fluid_dropdown = [{'label': f, 'value': f} for f in
            np.sort(dataset[mask_well & mask_geom & mask_form & mask_field
                & mask_latlen & mask_fracs]['Fluido_gor'].unique())]
    
    # Append 'select all' option
    if fluid_dropdown:
        fluid_dropdown.insert(0, {'label': 'Seleccionar todos', 'value': 'ALL'})

    #----------------------------------------
    # Update field dropdown
    #----------------------------------------
    field_dropdown = []

    if 'ALL' in field:
        field_dropdown = [{'label': f, 'value': f, 'disabled': True}
            for f in np.sort((
            dataset[mask_well & mask_geom & mask_form & mask_fluid & mask_latlen
            & mask_fracs]['Empresa']
            + ' > ' + dataset[mask_well & mask_geom & mask_form & mask_fluid
            & mask_latlen & mask_fracs]['Yacimiento']).unique())]
    else:
        field_dropdown = [{'label': f, 'value': f}
            for f in np.sort((
            dataset[mask_well & mask_geom & mask_form & mask_fluid & mask_latlen
            & mask_fracs]['Empresa']
            + ' > ' + dataset[mask_well & mask_geom & mask_form & mask_fluid
            & mask_latlen & mask_fracs]['Yacimiento']).unique())]
    
    # Append 'select all' option
    if field_dropdown:
        field_dropdown.insert(0, {'label': 'Seleccionar todos', 'value': 'ALL'})

    #----------------------------------------
    # Update wellnames dropdown
    #----------------------------------------
    mask = (mask_well & mask_geom & mask_form & mask_fluid & mask_field
        & mask_latlen & mask_fracs)
    dataset_filtered = dataset[mask]

    wellnames_dropdown = [{'label': w, 'value': w} for w in
        dataset_filtered['Pozo_Form'].tolist()]

    #----------------------------------------
    # Update user selection data and values
    #----------------------------------------
    user_selection = json.dumps({
        'geometry': geometry,
        'fluid': fluid,
        'field': field
    })

    # Update geometry values
    for geom in geometry:
        if geom not in [each['value'] for each in geometry_dropdown]:
            geometry.remove(geom)

    # Update fluid values
    for f in fluid:
        if f not in [each['value'] for each in fluid_dropdown]:
            field.remove(f)

    # Update field values
    for f in field:
        if f not in [each['value'] for each in field_dropdown]:
            field.remove(f)

    # Update lateral length min and max
    latlen_min = dataset[mask_well & mask_geom & mask_form & mask_fluid
        & mask_field & mask_fracs]['Rama'].min()
    latlen_max = dataset[mask_well & mask_geom & mask_form & mask_fluid
        & mask_field & mask_fracs]['Rama'].max()

    # Update fracs min and max
    fracs_min = dataset[mask_well & mask_geom & mask_form & mask_fluid
        & mask_field & mask_latlen]['Fracturas'].min()
    fracs_max = dataset[mask_well & mask_geom & mask_form & mask_fluid
        & mask_field & mask_latlen]['Fracturas'].max()

    return (geometry_dropdown, geometry, fluid_dropdown, fluid,
        field_dropdown, field, wellnames_dropdown, user_selection,
        latlen_min, latlen_max, latlen_min, latlen_max, latlen_min, latlen_max,
        fracs_min, fracs_max, fracs_min, fracs_max, fracs_min, fracs_max)


@app.callback(
    Output('maps-filtered-data', 'data'),

    Input('maps-wells-dropdown', 'value')
)
def filter_dataset(selected_wells):
    '''
    Queries database and returns a dataset stored on json based on wells selection.

    Params:
        selected_wells (list of str): contains the wells from dropdown selection

    Returns:
        maps-filtered-data (str): json with selected wells data from DB
    '''
    dataset = db.filter_dataset(selected_wells)
    
    return dataset.to_json(date_format='iso', orient='split')


@app.callback(
    Output('maps-wells-info-table', 'data'),

    Input('maps-filtered-data', 'data'),
)
def update_wells_info_table(filtered_data_json):
    '''
    Updates wells info table based on wells selected.

    Params:
        filtered_data_json ():

    Returns:
        info_table_rows (): 
    '''
    
    # JSON to pandas dataFrame
    dataset = pd.read_json(filtered_data_json, orient='split')

    # Order by wellname, TdP, qo_ef, qg_ef
    dataset.sort_values(['Pozo_Form', 'TdP', 'qo_ef', 'qg_ef'], inplace=True)
    dataset.reset_index(drop=True)

    # Get wellnames
    wellnames = dataset['Pozo_Form'].unique()

    # Build table
    info_table = pd.DataFrame({})
    for wellname in wellnames:
        dff = dataset[dataset['Pozo_Form'] == wellname]

        aux_dict = {
            'Pozo_Form_P': [wellname],
            'MinFecha': [dff['MinFecha'].iloc[-1].split('T')[0]],
            'Np': [dff['Acu_Pet'].iloc[-1]],
            'Gp': [dff['Acu_Gas'].iloc[-1]],
            'Fracturas': [dff['Fracturas'].iloc[-1]],
            'Rama': [dff['Rama'].iloc[-1]],
            'qo_ef_peak': [dff['qo_ef'].max()],
            'qg_ef_peak': [dff['qg_ef'].max()],
            'qo_avg': [dff['qo_avg'].iloc[-1]],
            'qg_avg': [dff['qg_avg'].iloc[-1]]
        }

        aux_df = pd.DataFrame.from_dict(aux_dict)
        info_table = pd.concat([info_table, aux_df])

    info_table_rows = info_table.to_dict('records')

    # Format rows
    for row in info_table_rows:
        row['Np'] = '{:,.0f}'.format(row['Np'])
        row['Gp'] = '{:,.0f}'.format(row['Gp'])
        row['Rama'] = '{:,.0f}'.format(row['Rama'])
        row['qo_ef_peak'] = '{:,.2f}'.format(row['qo_ef_peak'])
        row['qg_ef_peak'] = '{:,.2f}'.format(row['qg_ef_peak'])
        row['qo_avg'] = '{:,.2f}'.format(row['qo_avg'])
        row['qg_avg'] = '{:,.2f}'.format(row['qg_avg'])

    return info_table_rows
    
    
@app.callback(
    Output('map', 'figure'),

    [Input('map_type', 'value'),
    Input('maps-overlap-wells', 'value')])
def show_map_type(map_type, overlap_wells):
    '''
    Updates the map style based on radio item selection.

    Params:
        map_type (str | None): dropdown selection. None value makes no changes
            on map figure.
        overlap_wells (list of str): contains map configuration from checklist

    Returns:
        fig (plotly.go.Figure): updated map

    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    dff_grid = df_grid.copy()

    # Wells locations
    w_locations = go.Scattermapbox(
        name = 'Pozos',
        lon = wells_props['Coordenadax'],
        lat = wells_props['Coordenaday'],
        mode = 'markers',
        marker = dict(
            color = '#000000',
            size = 6,
            symbol = 'circle',
            showscale = False
        ),
        unselected = {'marker': {'opacity': 0.9}},
        selected = {
            'marker': {
                'opacity': 1,
                'size': 10,
                'color': '#00ff44'
            }
        },
        hoverinfo = 'text',
        hovertext = wells_props['Pozo_Form'],
        customdata = wells_props['Pozo_Form']
    )

    # Map locations (most common for all maps)
    locations_name = None
    locations_lon = dff_grid['x']
    locations_lat = dff_grid['y']
    locations_mode = 'markers'
    locations_marker = dict(
        size = 0,
        symbol = 'circle',
        showscale = False
    )
    locations_unselected = {'marker': {'opacity': 0}}
    locations_selected = {
        'marker': {
            'opacity': 1,
            'size': 5,
            'color': '#ff0000'
        }
    }
    locations_hoverinfo = None
    locations_hovertext = None
    locations_customdata = dff_grid.index

    # Maps layout (most common for all maps)
    layout_margin = dict(l=6, r=6, b=6, t=6)
    layout_uirevision = 'foo' #preserves state of figure/map after callback activated
    layout_clickmode = 'event+select'
    layout_hovermode = 'closest'
    layout_hoverdistance = 500
    layout_mapbox = dict(
        accesstoken = mapbox_acces_token,
        bearing = 0,
        center = dict(
            lat = -39.0862187,
            lon = -69.19757656
        ),
        pitch = 0,
        zoom = 5
    )
    layout_showlegend = False
    
    # Base map
    if map_type == 'BASE':
        locations_name = 'Coord'

        layout_mapbox['style'] = 'mapbox://styles/manuelrfdc/cket0m9qa40k219qstg9yb2sz'
    
    # Toc map
    elif map_type == 'TOC':
        locations_hoverinfo = 'text'
        locations_hovertext = dff_grid['toc']
        
        layout_mapbox['style'] = 'mapbox://styles/manuelrfdc/ckq15212g9tb018mu3i6g2cqp'
    
    # Thickness map
    elif map_type == 'THICKNESS':
        locations_hoverinfo = 'text'
        locations_hovertext = dff_grid['espesor']
    
        layout_mapbox['style'] = 'mapbox://styles/manuelrfdc/ckq153o6c3gxh17s5asgnxncr'
    
    #Ro map
    elif map_type == 'RO':
        locations_hoverinfo = 'text'
        locations_hovertext = dff_grid['madurez']

        layout_mapbox['style'] = 'mapbox://styles/manuelrfdc/ckq154jxb68bd17mwi03r0w4d'

    # Fluid map
    elif map_type == 'FLUID':
        locations_name = 'Coord'

        layout_mapbox['style'] = 'mapbox://styles/manuelrfdc/ckpy5hbst0bbh17s25olatbvl'

    # Overpressure map
    elif map_type == 'OVERPRESSURE':
        locations_name = 'Coord'

        layout_mapbox['style'] = 'mapbox://styles/santijav/cksg494o84mfs17n143laydd2'
        layout_mapbox['accesstoken'] = 'pk.eyJ1Ijoic2FudGlqYXYiLCJhIjoiY2tvdTl1NnFvMGIxZDJ3bzdtNjU3ZXVqZyJ9.3B3UhWvxuMD925XhrSB1Cw'
    
    # Build map locations and layout
    locations = go.Scattermapbox(
        name = locations_name,
        lon = locations_lon,
        lat = locations_lat,
        mode = locations_mode,
        marker = locations_marker,
        unselected = locations_unselected,
        selected = locations_selected,
        hoverinfo = locations_hoverinfo,
        hovertext = locations_hovertext,
        customdata = locations_customdata
    )
        
    layout = dict(
        margin = layout_margin,
        uirevision = layout_uirevision,
        clickmode = layout_clickmode,
        hovermode = layout_hovermode,
        hoverdistance = layout_hoverdistance,
        mapbox = layout_mapbox,
        showlegend = layout_showlegend
    )

    if overlap_wells: locations = [locations, w_locations]

    return go.Figure(data=locations, layout=layout)

    
# Thickness,TOC and RO values callback
@app.callback(
    [Output('thickness', 'value'),
    Output('toc', 'value'),
    Output('ro', 'value'),
    Output('rama', 'value'),
    Output('fracturas', 'value'),
    Output('maps-wells-dropdown', 'value'),
    Output('reset_plot', 'n_clicks')],

    [Input('map', 'clickData'),
    Input('map', 'selectedData'),
    Input('reset_plot', 'n_clicks'),
    Input('maps-wells-clear', 'n_clicks')],

    [State('maps-wells-dropdown', 'value'),
    State('thickness', 'value'),
    State('toc', 'value'),
    State('ro', 'value'),
    State('rama', 'value'),
    State('fracturas', 'value')])
def update_toc_thickness_values(clickData, map_selected_data, reset_plot,
    wells_clear, wells_selected, thickness, toc, ro, rama, fracturas):
    '''
    Updates thickness, toc, ro inputs and wells dropdown based on the data given
    by click on the map.

    Params:
        clickData (None | str | dict): contains click data from map
        map_selected_data (None | dict): contains map selected data
        reset_plot (None | int): number of clicks on reset plot button
        wells_selected (list of str): contains the wells from dropdown selection
        thickness (float | None): value from inputcomponent
        toc (float | None): value from input component
        ro (float | None): value from input component
        rama (float): value from input component
        fracturas (float): value from input component

    Returns:
        thickness (float | None): value to input component
        toc (float | None): value to input component
        ro (float | None): value to input component
        rama (float): value to input component
        fracturas (float): value to input component
        maps-wells-dropdown (list of str): selected wells to dropdown values
        reset_plot_clicks (int): number of clicks on reset plot button
    '''

    if not wells_selected: wells_selected = []
    if reset_plot: return None, None, None, 2500, 35, [], 0

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if 'wells-clear' in trigger_id and wells_clear:
        return thickness, toc, ro, rama, fracturas, [], 0

    dff_grid = df_grid.copy()

    if map_selected_data and ('lassoPoints' in map_selected_data):
        # Filter selected points
        lasso_data = pd.DataFrame(map_selected_data['points']).dropna(
            subset=['customdata'])
        lasso_wells = lasso_data.loc[lasso_data['curveNumber'] == 1]['customdata'].values

        # Append lasso wells to wells_selected
        for w in lasso_wells:
            if w not in wells_selected:
                wells_selected.append(w)
    else:
        lasso_wells = []

    if clickData:
        if isinstance(clickData['points'][0]['customdata'], str):
            well_name = clickData['points'][0]['customdata']

            if wells_selected:
                if well_name in wells_selected:
                    if well_name not in lasso_wells:
                        wells_selected.remove(well_name)
                else:
                    wells_selected.append(well_name)
            else:
                wells_selected = [well_name]

            return thickness, toc, ro, rama, fracturas, wells_selected, 0
        else:
            index = clickData['points'][0]['customdata']
            toc = np.round(dff_grid.loc[index, 'toc'], 2)
            thickness = np.round(dff_grid.loc[index, 'espesor'], 2)
            ro = np.round(dff_grid.loc[index, 'madurez'], 2)

            return thickness, toc, ro, rama, fracturas, wells_selected, 0
    else:
        return None, None, None, rama, fracturas, wells_selected, 0
    
# Qo and Cumulative plots (connected with Output('maps-wells-dropdown','value'))
@app.callback(
    [Output('oil_rates', 'figure'),
    Output('oil_cumulatives', 'figure'),
    Output('gas_rates', 'figure'),
    Output('gas_cumulatives', 'figure'),
    Output('water_rates', 'figure'),
    Output('water_cumulatives', 'figure'),
    Output('corr-toast-oil', 'is_open'),
    Output('corr-toast-gas', 'is_open'),
    Output('maps-history-forecasts-table', 'data'),
    Output('maps-forecasts', 'data')],
    
    [Input('maps-wells-dropdown', 'value'),
    Input('maps-synth-wellname', 'value'),
    Input('maps-synth-date-picker', 'date'),
    Input('maps-filtered-data', 'data'),
    Input('thickness', 'value'),
    Input('toc', 'value'),
    Input('ro', 'value'),
    Input('rama', 'value'),
    Input('fracturas', 'value'),
    Input('t_peak', 'value'),
    Input('target_depth', 'value'),
    Input('map_corr_uncertainty', 'value'),
    Input('maps-frac-normalize', 'value'),
    Input('maps-log-scale', 'value'),
    Input('corr_selected', 'value')],
    
    [State('oil_rates', 'figure'),
    State('oil_cumulatives', 'figure'),
    State('gas_rates', 'figure'),
    State('gas_cumulatives', 'figure'),
    State('water_rates', 'figure'),
    State('water_cumulatives', 'figure')])
def update_figs_n_tables(wells_selected, synth_wellname, synth_mindate, 
    filtered_data_maps_json, thickness, toc, ro, rama, fracturas, t_peak,
    target_depth, uncertainty, frac_normalize, log_scale, corr_selected,
    prev_qo_fig_dict, prev_cumo_fig_dict, prev_qg_fig_dict, prev_cumg_fig_dict,
    prev_qw_fig_dict, prev_cumw_fig_dict):
    '''
    Updates rates and cumulatives plots. Also shows a warning toast if the
    correlation boundaries has been reached.

    Params:
        wells_selected (list of str): contains the wells from dropdown selection
        synth_wellname
        synth_mindate
        thickness (float | None): value from input component
        toc (float | None): value from input component
        ro (float | None): value from input component
        rama (float): value from input component
        fracturas (float): value from input component
        frac_normalize (list of str): config for rates and cumulatives plots for
            oil and gas. Contains several of the following:
            - 'LOG_SCALE': log scale
            - 'FRAC_NORMALIZE': normalize rates by num of fractures
        corr_selected (str | None): fluid correlation for forecast calculation
        map_selected_data (None | dict): contains map selected data
        reset_plot (None | int): number of clicks on reset plot button
        prev_qo_fig_dict (dict | None): current state for oil rates plot
        prev_cumo_fig_dict (dict | None): current state for oil cumulatives plot
        prev_qg_fig_dict (dict | None): current state for gas rates plot
        prev_cumg_fig_dict (dict | None): current state for gas cumulatives plot
        prev_qw_fig_dict (dict | None): current state for gas rates plot
        prev_cumw_fig_dict (dict | None): current state for gas cumulatives plot

    Returns:
        qo_fig (plotly.go.figure): represents the figure for oil rates forecasts
        cumo_fig (plotly.go.figure): represents the figure for oil cumulatives
            forecasts
        qg_fig (plotly.go.figure): represents the figure for gas rates forecasts
        cumg_fig (plotly.go.figure): represents the figure for gas cumulatives
            forecasts
        qw_fig (plotly.go.figure): represents the figure for water rates forecasts
        cumw_fig (plotly.go.figure): represents the figure for water cumulatives
            forecasts
        show_toast_oil (bool): shows/hides oil correlation warning toast
        show_toast_gas (bool): shows/hides gas correlation warning toast
        reset_plot_n_clicks (int): number of click for reset plot
    '''

    #----------------------------------------
    # Initial setup
    #----------------------------------------
    show_toast_oil = False
    show_toast_gas = False
    pxx = ['P10', 'P90', 'P50']

    axis_config = {
        'gridcolor':'#eee',
        'linecolor':'#444',
        'zerolinecolor':'#eee',
        'mirror': True,
        'rangemode': 'nonnegative'
    }

    plot_layout = Layout(
        plot_bgcolor = 'rgba(0,0,0,0)',
        title = {'y':0.98, 'x':0.5, 'xanchor':'center', 'yanchor':'top'},
        height = 362,
        margin = dict(l=20, r=20, b=20, t=35),
        yaxis = axis_config,
        xaxis = axis_config,
        xaxis_title = 'Días',
        showlegend = False
    )

    # If is first time, build base plots
    if (prev_qo_fig_dict is None):

        # Rates plots
        qo_fig = go.Figure(layout=plot_layout)
        qg_fig = go.Figure(layout=plot_layout)
        qw_fig = go.Figure(layout=plot_layout)

        qo_fig.update_layout(
            title_text = 'Caudal de Petróleo',
            yaxis_title = 'qo [m3/d]'
        )       

        qg_fig.update_layout(
            title_text = 'Caudal de Gas',
            yaxis_title = 'qg [Mm3/d]'
        )

        qw_fig.update_layout(
            title_text = 'Caudal de Agua',
            yaxis_title = 'qw [m3/d]'
        )

        # Cumulatives plots
        cumo_fig = go.Figure(layout=plot_layout)
        cumg_fig = go.Figure(layout=plot_layout)
        cumw_fig = go.Figure(layout=plot_layout)

        cumo_fig.update_layout(
            title_text = 'Acumulada de Petróleo',
            yaxis_title = 'Np [m3]'
        )

        cumg_fig.update_layout(
            title_text = 'Acumulada de Gas',
            yaxis_title = 'Gp [Mm3]'
        )

        cumw_fig.update_layout(
            title_text = 'Acumulada de Agua',
            yaxis_title = 'Wp [m3]'
        )
    
    else:
        # Remove all historical oil wells
        wellnames = [trace.get('name') for trace in prev_qo_fig_dict['data']]
        j = 0
        for i, w in enumerate(wellnames):
            if w not in pxx:
                del prev_qo_fig_dict['data'][i - j]
                del prev_cumo_fig_dict['data'][i - j]
                j += 1

        # Remove all historical gas wells
        wellnames = [trace.get('name') for trace in prev_qg_fig_dict['data']]
        j = 0
        for i, w in enumerate(wellnames):
            if w not in pxx:
                del prev_qg_fig_dict['data'][i - j]
                del prev_cumg_fig_dict['data'][i - j]
                j += 1

        # Remove all historical gas wells
        wellnames = [trace.get('name') for trace in prev_qw_fig_dict['data']]
        j = 0
        for i, w in enumerate(wellnames):
            if w not in pxx:
                del prev_qw_fig_dict['data'][i - j]
                del prev_cumw_fig_dict['data'][i - j]
                j += 1

        # if thickness and toc and ro and rama and fracturas:
        for p in pxx:
            try:
                # p is in plot
                wells_in_plot = [trace.get('name') for trace in prev_qo_fig_dict['data']]
                pos = wells_in_plot.index(p)

                del prev_qo_fig_dict['data'][pos]
                del prev_cumo_fig_dict['data'][pos]
            except:
                # p is not in plot
                pass

        # if thickness and toc and ro and rama and fracturas:
        for p in pxx:
            try:
                # p is in plot
                wells_in_plot = [trace.get('name') for trace in prev_qg_fig_dict['data']]
                pos = wells_in_plot.index(p)

                del prev_qg_fig_dict['data'][pos]
                del prev_cumg_fig_dict['data'][pos]
            except:
                # p is not in plot
                pass

        # if thickness and toc and ro and rama and fracturas:
        for p in pxx:
            try:
                # p is in plot
                wells_in_plot = [trace.get('name') for trace in prev_qw_fig_dict['data']]
                pos = wells_in_plot.index(p)

                del prev_qw_fig_dict['data'][pos]
                del prev_cumw_fig_dict['data'][pos]
            except:
                # p is not in plot
                pass

        # Re build prev plots
        qo_fig = go.Figure(prev_qo_fig_dict)
        cumo_fig = go.Figure(prev_cumo_fig_dict)
        qg_fig = go.Figure(prev_qg_fig_dict)
        cumg_fig = go.Figure(prev_cumg_fig_dict)
        qw_fig = go.Figure(prev_qw_fig_dict)
        cumw_fig = go.Figure(prev_cumw_fig_dict)

    # If there are historical wells selected, add them to plot
    if wells_selected:
        dataset_filtered = pd.read_json(filtered_data_maps_json, orient='split')

        for wellname in wells_selected:
            
            # Get well data
            well_df = dca.extract_single_well(dataset_filtered, wellname, filter=True)
            dff = wells_props[wells_props['Pozo_Form'] == wellname]
            t_history = well_df['TdP']
            qo_history = well_df['qo_ef']
            cumo_history = well_df['Acu_Pet']
            qg_history = well_df['qg_ef']
            cumg_history = well_df['Acu_Gas']
            qw_history = well_df['qw_ef']
            cumw_history = np.add.accumulate(
                np.append(
                    t_history[0]*qw_history[0],
                    np.multiply(np.diff(t_history), qw_history[1:])))

            # If FRAC_NORMALIZE and well has fracs, recalculate rates and cumulatives
            if frac_normalize and dff['Fracturas'].notna().all():
                qo_history = qo_history.copy() * fracturas/dff['Fracturas'].values
                cumo_history = np.add.accumulate(
                    np.append(
                        t_history[0] * qo_history[0],
                        np.multiply(np.diff(t_history), qo_history[1:])))

                qg_history = qg_history.copy() * fracturas/dff['Fracturas'].values
                cumg_history = np.add.accumulate(
                    np.append(
                        t_history[0] * qg_history[0],
                        np.multiply(np.diff(t_history), qg_history[1:])))

                qw_history = qw_history.copy() * fracturas/dff['Fracturas'].values
                cumw_history = np.add.accumulate(
                    np.append(
                        t_history[0] * qw_history[0],
                        np.multiply(np.diff(t_history), qw_history[1:])))

            # Add trace to rates fig
            qo_fig.add_trace(
                go.Scatter(
                    name = wellname,
                    x = t_history,
                    y = qo_history,
                    mode = 'lines',
                    hovertemplate = 'qo = %{y:,.0f}' + '<br>TdP = %{x:,.0f}'
                )
            )

            qg_fig.add_trace(
                go.Scatter(
                    name = wellname,
                    x = t_history,
                    y = qg_history,
                    mode = 'lines',
                    hovertemplate = 'qg = %{y:,.0f}' + '<br>TdP = %{x:,.0f}'
                )
            )

            qw_fig.add_trace(
                go.Scatter(
                    name = wellname,
                    x = t_history,
                    y = qw_history,
                    mode = 'lines',
                    hovertemplate = 'qw = %{y:,.0f}' + '<br>TdP = %{x:,.0f}'
                )
            )

            # Add trace to cumulatives fig
            cumo_fig.add_trace(
                go.Scatter(
                    name = wellname,
                    x = t_history,
                    y = cumo_history,
                    mode = 'lines',
                    hovertemplate = 'Np = %{y:,.0f}' + '<br>TdP = %{x:,.0f}'
                )
            )

            cumg_fig.add_trace(
                go.Scatter(
                    name = wellname,
                    x = t_history,
                    y = cumg_history,
                    mode = 'lines',
                    hovertemplate = 'Gp = %{y:,.0f}' + '<br>TdP = %{x:,.0f}'
                )
            )

            cumw_fig.add_trace(
                go.Scatter(
                    name = wellname,
                    x = t_history,
                    y = cumw_history,
                    mode = 'lines',
                    hovertemplate = 'Wp = %{y:,.0f}' + '<br>TdP = %{x:,.0f}'
                )
            )
        
        # Update layout
        qo_fig.update_layout(showlegend = True)
        cumo_fig.update_layout(showlegend = True)
        
        qg_fig.update_layout(showlegend = True)
        cumg_fig.update_layout(showlegend = True)

        qw_fig.update_layout(showlegend = True)
        cumw_fig.update_layout(showlegend = True)
    
    # If there is correlation data make forecast
    if thickness and toc and ro and rama and fracturas:

        # If corr_selected is AUTO, calculate fluid
        if corr_selected == 'AUTO': corr_selected = mcorr.calculate_fluid(ro)

        if corr_selected == 'OIL':
            # Values from oil correlation
            well_P50, well_P90, well_P10 = mcorr.oil_correlation(rama, fracturas,
                toc, ro, thickness, t_peak, target_depth, uncertainty)

            # Add trace to oil rates fig
            well_P10['fill'], well_P50['fill'], well_P90['fill'] = None, None, 'tonexty'
            well_P10['width'], well_P50['width'], well_P90['width'] = 0.1, 3, 0.1

            for well in [well_P10, well_P90, well_P50]:
                qo_fig.add_trace(
                    go.Scatter(
                        name = well['wellname'],
                        fill = well['fill'],
                        x = well['t_forecast'],
                        y = well['qo_forecast'],
                        mode = 'lines',
                        hovertemplate = 'qo = %{y:,.0f}' + '<br>TdP = %{x:,.0f}' \
                            + '<br>'.join(('',
                            f'<b>b</b>: {well["b"]:,.2f}',
                            f'<b>d_hyp [% 1/d]</b>: {well["d_hyp"] * 100:,.2f}',
                            f'<b>d_hyp [% 1/yr]</b>: {well["d_hyp"] * 365.25 * 100:,.2f}')),
                        line = dict(color='#6A9949', width=well['width'], dash='dash')
                    )
                )

                cumo_fig.add_trace(
                    go.Scatter(
                        name = well['wellname'],
                        fill = well['fill'],
                        x = well['t_forecast'],
                        y = well['cumo_forecast'],
                        mode = 'lines',
                        hovertemplate = 'Np = %{y:,.0f}' + '<br>TdP = %{x:,.0f}',
                        line = dict(color='#6A9949', width=well['width'], dash='dash')
                    )
                )

            # Show warning toast for correlation recommended values
            if toc and not (3.75 <= toc <= 5): show_toast_oil = True
            if ro and not (0.9 <= ro <= 1.3): show_toast_oil = True
            if thickness and not (100 <= thickness <= 220): show_toast_oil = True
            if fracturas and not (20 <= fracturas <= 60): show_toast_oil = True

        elif corr_selected == 'GAS':
            # Values from oil correlation
            well_P50, well_P90, well_P10 = mcorr.gas_correlation(rama, fracturas,
                toc, ro, thickness, t_peak, target_depth, uncertainty)
            
            # Add trace to oil rates fig
            well_P10['fill'], well_P50['fill'], well_P90['fill'] = None, None, 'tonexty'
            well_P10['width'], well_P50['width'], well_P90['width'] = 0.1, 3, 0.1

            for well in [well_P10, well_P90, well_P50]:
                qg_fig.add_trace(
                    go.Scatter(
                        name = well['wellname'],
                        fill = well['fill'],
                        x = well['t_forecast'],
                        y = well['qg_forecast'],
                        mode = 'lines',
                        hovertemplate = 'qg = %{y:,.0f}'+'<br>TdP = %{x:,.0f}'+
                        '<br>'.join((
                        '',
                        f'<b>b</b>: {well["b"]:,.2f}',
                        f'<b>d_hyp [% 1/d]</b>: {well["d_hyp"] * 100:,.2f}',
                        f'<b>d_hyp [% 1/yr]</b>: {well["d_hyp"] * 365.25 * 100:,.2f}'
                        )),
                        line = dict(color='#994949', width=well['width'], dash='dash')
                    )
                )

                cumg_fig.add_trace(
                    go.Scatter(
                        name = well['wellname'],
                        fill = well['fill'],
                        x = well['t_forecast'],
                        y = well['cumg_forecast'],
                        mode = 'lines',
                        hovertemplate = 'Gp = %{y:,.0f}' + '<br>TdP = %{x:,.0f}',
                        line = dict(color='#994949', width=well['width'], dash='dash')
                    )
                )

            # Show warning toast for correlation recommended values
            if toc and not (3.75 <= toc <= 5.75): show_toast_gas = True
            if ro and not (1.4 <= ro <= 1.6): show_toast_gas = True
            if thickness and not (150 <= thickness <= 280): show_toast_gas = True
            if fracturas and not (10 <= fracturas <= 60): show_toast_gas = True

    #----------------------------------------
    # Plots config
    #----------------------------------------
    if log_scale:
        qo_fig.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
        qg_fig.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
        qw_fig.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
    else:
        qo_fig.update_yaxes(type = 'linear')
        qg_fig.update_yaxes(type = 'linear')
        qw_fig.update_yaxes(type = 'linear')

    #----------------------------------------
    # Generate table
    #----------------------------------------
    table = pd.DataFrame({})

    # If forecast exists, append synthetic wells to table dataframe
    if 'well_P50' in locals():
        for well in [well_P10, well_P50, well_P90]:
            aux_dict = {
                'FORECAST': np.repeat(well['wellname'], len(well['t_forecast'])),
                'TdP': well['t_forecast'],
                'qo': well['qo_forecast'],
                'Np': well['cumo_forecast'],
                'GOR': well['GOR'],
                'qg': well['qg_forecast'],
                'Gp': well['cumg_forecast'],
            }

            aux_df = pd.DataFrame.from_dict(aux_dict)
            table = pd.concat([table, aux_df])

    # Set rows
    rows = table.to_dict('records')

    # Format rows
    for row in rows:
        row['TdP'] = '{:,.0f}'.format(row['TdP'])
        row['qo'] = '{:,.2f}'.format(row['qo'])
        row['Np'] = '{:,.0f}'.format(row['Np'])
        row['GOR'] = '{:,.0f}'.format(row['GOR'])
        row['qg'] = '{:,.3f}'.format(row['qg'])
        row['Gp'] = '{:,.0f}'.format(row['Gp'])

    #----------------------------------------
    # Process forecasts to store in session
    #----------------------------------------
    synthetic = {}
    if len(table):
        for well in [well_P10, well_P50, well_P90]:
            estimate = well['wellname'].split()[0]
            if synth_wellname:
                assert(('_' not in synth_wellname) and (' ' not in synth_wellname))
                wellname = f'{synth_wellname}:Correlation-{estimate}'
            else:
                now = datetime.now()
                wellname = f'{now.year}{now.month}{now.day}{now.hour:02}{now.minute:02}:Correlation-{estimate}'
            synthetic[wellname] = {'wellname': wellname}
            synthetic[wellname]['well_data'] = pd.DataFrame(
                {
                    'TdP': np.array([0]),
                    'qo_ef': np.array([0]),
                    'Acu_Pet': np.array([0]),
                    'qg_ef': np.array([0]),
                    'Acu_Gas': np.array([0]),
                    'GOR_ef': np.array([0]),
                    'qw_ef': np.array([0]),
                    'MinFecha': synth_mindate,
                    'empresa': '-',
                    'areayacimiento': '-',
                    'cuenca': '-'
                }
            )

            synthetic[wellname]['t_forecast'] = well['t_forecast']
            synthetic[wellname]['qo_forecast'] = well['qo_forecast']
            synthetic[wellname]['cumo_forecast'] = well['cumo_forecast']
            synthetic[wellname]['GOR_forecast'] = well['GOR']
            synthetic[wellname]['qg_forecast'] = well['qg_forecast']
            synthetic[wellname]['cumg_forecast'] = well['cumg_forecast'	]
            synthetic[wellname]['dca_model'] = 'HM'
            synthetic[wellname]['b'] = well['b']
            synthetic[wellname]['d_hyp'] = well['d_hyp'] * 365.25 * 100
            synthetic[wellname]['d_exp'] = 'None'
        
    maps_forecasts_json = dca.serialize_forecast(synthetic)

    return (qo_fig, cumo_fig, qg_fig, cumg_fig, qw_fig, cumw_fig, show_toast_oil, 
        show_toast_gas, rows, maps_forecasts_json)


@app.callback(
    [Output('maps-wells-info-container', 'is_open'),
    Output('maps-wells-info-button', 'n_clicks'),
    Output('maps-wells-info-button', 'className')],

    Input('maps-wells-info-button', 'n_clicks'),

    [Input('maps-wells-info-container', 'is_open'),
    State('maps-wells-info-button', 'className')]
)
def show_hide_wells_info(button_click, container_open, className):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    if button_click:
        if 'pressed' in className:
            return ~container_open, 0, 'ribbon-btn'
        else:
            return ~container_open, 0, 'ribbon-btn-pressed'

    return False, 0, className


@app.callback(
    Output('maps-db-toast', 'data'),

    Input('maps-forecasts-to-db', 'n_clicks'),

    [State('maps-forecasts', 'data'),
    State('ro', 'value'),
    State('corr_selected', 'value'),
    State('session', 'data')]
)
def export_maps_forecast_db(export_button_click, maps_forecasts, ro,
    corr_selected, session):
    '''
    Exports oil forecasts to DB and shows toast with results

    Params:
        - export_button_click (int):
        - maps_forecasts (str): json
        - session (str): json

    Returns:
        - toast (dict):

    TODO: COMPLETAR DOCSTRING

    '''

    toast_header = 'Exportar a DB'

    # If button is clicked, export to DB
    if export_button_click and len(json.loads(maps_forecasts)):
        try:
            if session and 'LOGGED_IN' in session: session_dict = json.loads(session)

            if corr_selected == 'OIL':
                fluid = 'oil'
            elif corr_selected == 'GAS':
                fluid = 'gas'
            else:
                fluid = mcorr.calculate_fluid(ro).lower()

            db.forecasts_to_sql(maps_forecasts, session_dict, fluid=fluid)
            toast_msg = 'Pronósticos guardados en DB correctamente.'
            toast_icon = "success"
            toast_duration = 4000 # Milisecs

        except Exception as err:
            toast_msg = f'Ocurrió un error al guardar los pronósticos en DB [{err}]'
            toast_icon = "warning"
            toast_duration = None

        open_toast = True
    else:
        return None

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

    return json.dumps(toast)


@app.callback(
    [Output('maps-geometry-container', 'label'),
    Output('maps-fluid-container', 'label'),
    Output('maps-field-container', 'label'),
    Output('maps-wells-container', 'label')],

    [Input('maps-geometry-dropdown', 'value'),
    Input('maps-fluid-dropdown', 'value'),
    Input('maps-field-dropdown', 'value'),
    Input('maps-wells-dropdown', 'value')]
)
def update_dropdowns_labels(*args):
    '''TODO: COMPLETAR DOCSTRING'''
    
    def count_elements(dropdown):
        if dropdown is None:
            return 0
        elif 'ALL' in dropdown:
            return 1
        else:
            return len(dropdown)
    
    return [str(count_elements(dropdown)) + ' seleccionados' for dropdown in args]
    

@app.callback(
    [Output('maps-filter-sidebar-expanded', 'className'),
    Output('maps-filter-sidebar-collapsed', 'className'),
    Output('maps-container', 'className')],

    [Input('maps-filter-sidebar-collapse-btn', 'n_clicks'),
    Input('maps-filter-sidebar-expand-btn', 'n_clicks')]
)
def toggle_collapse_sidebar(*args):
    '''
    Expands or collapses sidebar through expand or collapse buttons.

    Params:
        - n_collapse (int): number of clicks on collapse button
        - n_expand (int): number of clicks on expand button

    Returns:
        - 
    
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''
    # Get elements that triggered the callback
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if 'filter-sidebar-collapse' in trigger_id:
        filter_sidebar_expanded_class = 'hide-element'
        filter_sidebar_collapsed_class = 'show-filter-sidebar-collapsed'
        main_container_class = 'left-collapsed'
    else:
        filter_sidebar_expanded_class = 'show-filter-sidebar-expanded'
        filter_sidebar_collapsed_class = 'hide-element'
        main_container_class = 'left-expanded' 

    return (filter_sidebar_expanded_class, filter_sidebar_collapsed_class,
        main_container_class)


@app.callback(
    [Output('maps-overlap-wells', 'className'),
    Output('maps-frac-normalize', 'className')],

    [Input('maps-overlap-wells', 'value'),
    Input('maps-frac-normalize', 'value')]
)
def toggle_on_off(overlap_wells_on, frac_normalize_on):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''
    
    if overlap_wells_on:
        overlap_wells_btn = 'toggle-switch-colored'
    else:
        overlap_wells_btn = 'toggle-switch'

    if frac_normalize_on:
        frac_normalize_btn = 'toggle-switch-colored'
    else:
        frac_normalize_btn = 'toggle-switch'
    
    return overlap_wells_btn, frac_normalize_btn


app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0)
            document.querySelector("#maps-history-forecasts-table button.export").click()
        return ""
    }
    """,
    Output('maps-export-table-xls', 'data-dummy'),
    Input('maps-export-table-xls', 'n_clicks')
)