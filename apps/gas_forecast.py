import dash
from datetime import datetime, date
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from plotly.graph_objects import Layout
from dash.dependencies import Input, Output, State
import dash_table as dt
import dash_daq as daq
from app import app
from core import decline_curve_analysis as dca
from core import database as db
from apps import common_components
from dash.dash import no_update
import re


#------------------------------------------------------------------------------
# Ribbon
#------------------------------------------------------------------------------
ribbon = html.Div([
    # Decline auto button
    html.Button([
        html.Img(
            src = '/assets/btn-decline-auto.png',
            className = 'ribbon-icon',
        ),
        html.P('Declinación auto')],
        id = 'gas-btn-decline-auto',
        className = 'ribbon-btn',
    ),
    
    # Decline manual button
    # html.Button([
    #     html.Img(
    #         src = '/assets/btn-decline-manual.png',
    #         className = 'ribbon-icon',
    #     ),
    #     html.P('Declinación manual')],
    #     id = 'gas-btn-decline-manual',
    #     className = 'ribbon-btn',
    # ),
    
    # Wells info button
    html.Button([
        html.Img(
            src = '/assets/btn-info.png',
            className = 'ribbon-icon',
        ),
        html.P('Info de pozos')],
        id = 'gas-wells-info-button',
        className = 'ribbon-btn',
    ),
    
    # Forecasts from DB button
    html.Button([
        html.Img(
            src = '/assets/db-down.png',
            className = 'ribbon-icon'
        ),
        html.P('Pronósticos DB')],
        id = 'gas-btn-forecasts-from-db',
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
        id = 'gas-forecasts-to-db',
    ),
    
    # Export to Excel button
    html.Button([
        html.Img(
            src = '/assets/excel.png',
            className = 'ribbon-icon'
        ),
        html.P('Exportar a Excel')],
        className = 'ribbon-btn',
        id = 'gas-export-table-xls',
        **{'data-dummy': ''}
    ),],
    id = 'gas-ribbon'
)

#------------------------------------------------------------------------------
# Layout
#------------------------------------------------------------------------------
layout = html.Div([
    #----------------------------------------
    # Store components
    #----------------------------------------
    # Store user forecasts
    dcc.Store(id='gas-forecasts', storage_type='memory'),

    # Store DB forecasts
    dcc.Store(id='gas-my_forecasts', storage_type='session'),

    # Store user current dropdown selection
    dcc.Store(id='gas-user-selection', storage_type='memory'),

    # Stores the filtered dataset
    dcc.Store(id = 'gas-filtered-data', storage_type = 'memory'),

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
            id = 'gas-filter-sidebar-collapse-btn',
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
                id = 'gas-date-picker',
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
                id = "gas-datepicker-clear",
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
                        id = 'gas-geometry-dropdown',
                        value = [],
                        options = [],
                        labelClassName = 'checklist-label',
                        inputClassName = 'checklist-checkbox',
                        className = 'sidebar-checklist'
                    )
                ],
                id = 'gas-geometry-container',
                toggleClassName = 'dropdown-btn'
            ),
            
            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "gas-geometry-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        # Formation filter
        html.H6('Formación', className = 'sidebar-filter-title'),

        html.Div([
            # Formation dropdown
            dbc.DropdownMenu(
                label = '0 seleccionados',
                children = [
                    dcc.Checklist(
                        id = 'gas-formation-dropdown',
                        value = [],
                        options = [],
                        labelClassName = 'checklist-label',
                        inputClassName = 'checklist-checkbox',
                        className = 'sidebar-checklist'
                    )
                ],
                id = 'gas-formation-container',
                toggleClassName = 'dropdown-btn'
            ),

            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "gas-formation-clear",
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
                        id = 'gas-field-dropdown',
                        value = [],
                        options = [],
                        labelClassName = 'checklist-label',
                        inputClassName = 'checklist-checkbox',
                        className = 'sidebar-checklist'
                    )
                ],
                id = 'gas-field-container',
                toggleClassName = 'dropdown-btn'
            ),
            
            # Clear button
            html.Button(
                html.Img(
                    src='assets/x.png',
                    className='sidebar-clear-icon'
                ),
                id = "gas-field-clear",
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
                id = 'gas-latlength-input-start',
                type = 'number',
                placeholder = 'Min',
                debounce = True,
                className = 'input-latlen'
            ),

            dcc.Input(
                id = 'gas-latlength-input-end',
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
                id = "gas-latlength-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        dcc.RangeSlider(id = 'gas-latlength-slider'),

        # Fracture stages filter
        html.H6('Fracturas', className = 'sidebar-filter-title'),

        html.Div([
            # Fractures inputs and slider
            dcc.Input(
                id = 'gas-fracs-input-start',
                type = 'number',
                placeholder = 'Min',
                debounce = True,
                className = 'input-latlen'
            ),

            dcc.Input(
                id = 'gas-fracs-input-end',
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
                id = "gas-fracs-clear",
                className = 'sidebar-clear-btn',
                n_clicks = 0
            )],

            className = 'filter-row'
        ),

        dcc.RangeSlider(id = 'gas-fracs-slider'),

        # Wellname filter
        html.Div([
            html.H6('Nombre de pozo', className = 'sidebar-filter-title'),

            html.Img(
                src = 'assets/exclamation.png',
                id = 'gas-select-all-warning',
                className = 'select-all-warning',
            ),

            dbc.Tooltip(
                'Se ocultó "Seleccionar todos" porque hay más de 250 pozos disponibles',
                target = "gas-select-all-warning",
            )],

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
                                id = 'gas-wells-dropdown',
                                value = [],
                                options = [],
                                labelClassName = 'checklist-label',
                                inputClassName = 'checklist-checkbox',
                                className = 'sidebar-checklist'
                            )
                        ],
                        id = 'gas-wells-container',
                        toggleClassName = 'dropdown-btn'
                    ),

                    # Clear button
                    html.Button(
                        html.Img(
                            src='assets/x.png',
                            className='sidebar-clear-icon'
                        ),
                        id = "gas-wells-clear",
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
        id = 'gas-filter-sidebar-expanded',
        className = 'show-filter-sidebar-expanded'
    ),

    # Collapsed sidebar
    html.Div([
        html.Button([
            html.Img(
                src = 'assets/filter.png',
                className='sidebar-expand-icon'
            )],
            id = 'gas-filter-sidebar-expand-btn',
            className = 'sidebar-expand-btn'
        )
        ],
        id = 'gas-filter-sidebar-collapsed',
        className = 'hide-element'
    ),
    
    #----------------------------------------
    # My forecasts sidebars
    #----------------------------------------
    # Expanded sidebar
    html.Div([
        html.Button([
            html.Img(
                src = 'assets/arrow-from-right.png',
                className='sidebar-collapse-icon'
            )],
            id = 'gas-db-sidebar-collapse-btn',
            className = 'right-sidebar-collapse-btn',
        ),

        html.Button([
            html.Img(
                src = 'assets/update.png',
                className='sidebar-expand-icon'
            )],
            id = 'gas-db-sidebar-update-btn',
            className = 'left-sidebar-collapse-btn',
        ),

        dbc.Tooltip(
            'Actualizar lista',
            target = "gas-db-sidebar-update-btn",
            placement = 'left',
        ),

        html.Br(),

        # Sidebar title
        html.H5('Pronósticos guardados', className = 'sidebar-main-title'),

        # Forecasts checklist
        dcc.Checklist(
            options = [],
            id = 'gas-db-checklist',
            labelClassName = 'checklist-label',
            inputClassName = 'checklist-checkbox',
            className = 'sidebar-checklist',
        )],

        id = 'gas-db-sidebar-expanded',
        className = 'hide-element',
    ),

    # Collapsed sidebar
    html.Div([
        html.Button([
            html.Img(
                src = 'assets/select-multiple.png',
                className='sidebar-expand-icon'
            )],
            id = 'gas-db-sidebar-expand-btn',
            className = 'sidebar-expand-btn'
        )],
        id = 'gas-db-sidebar-collapsed',
        className = 'hide-element'
    ),


    #----------------------------------------
    # Main content
    #----------------------------------------
    dbc.Container([
        #----------------------------------------
        # DCA auto controls
        #----------------------------------------
        dbc.Collapse([
            dbc.Card([
                dbc.CardHeader([
                    html.H4(
                        'Declinación automática',
                        className = 'card-title'
                    )]
                ),

                dbc.Row([
                    # Decline model column
                    dbc.Col([
                        html.H6(
                            'Modelo de declinación',
                            className = 'control-title'
                        ),
                        
                        dcc.Dropdown(
                            id = 'gas-dca-auto-model',
                            options = [
                                {'label': 'Hiperbólico', 'value': 'HYP'},
                                {'label': 'Hiperbólico modificado', 'value': 'HM'}
                            ],
                            multi = False,
                            value = 'HYP',
                            clearable = False,
                            searchable = False,
                            className = 'dropdown-control',
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 1},
                        sm = {'size': 12, 'order': 1},
                        md = {'size': 5, 'order': 1},
                        lg = {'size': 5, 'order': 1},
                        xl = {'size': 3, 'order': 1},
                    ),

                    # Exponential change column
                    dbc.Col([
                        html.H6(
                            'Cambio a exponencial',
                            className = 'control-title'
                        ),
                        
                        html.Div([
                            dcc.Dropdown(
                                id = 'gas-dca-auto-exp-start-method',
                                options = [
                                    {'label': 'Por tiempo (días)', 'value': 'EXP_START_TIME'},
                                    # {'label': 'Por declinación (%/año)', 'value': 'EXP_START_DT'}
                                ],
                                multi = False,
                                value = 'EXP_START_TIME',
                                clearable = False,
                                searchable = False,
                                className = 'dropdown-control',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 2},
                        sm = {'size': 10, 'order': 2},
                        md = {'size': 5, 'order': 2},
                        lg = {'size': 5, 'order': 2},
                        xl = {'size': 2, 'order': 2},
                    ),

                    # Exponential change input column
                    dbc.Col([
                        dcc.Input(
                            id = 'gas-dca-auto-exp-start-input',
                            type = 'number',
                            placeholder = 'días',
                            value = 2600,
                            debounce = True,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 3},
                        sm = {'size': 2, 'order': 3},
                        md = {'size': 2, 'order': 3},
                        lg = {'size': 2, 'order': 3},
                        xl = {'size': 1, 'order': 3},
                    ),

                    # Empty column
                    dbc.Col([],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 4},
                        sm = {'size': 1, 'order': 5},
                        md = {'size': 3, 'order': 5},
                        lg = {'size': 3, 'order': 5},
                        xl = {'size': 1, 'order': 4},
                    ),

                    # Years to forecast column
                    dbc.Col([
                        html.H6(
                            'Años a pronosticar',
                            className = 'control-title'
                        ),
                        
                        dcc.Input(
                            id = 'gas-dca-auto-forecast-end-time-input',
                            type = 'number',
                            placeholder = 'años',
                            value = 35,
                            debounce = True,
                            max = 50,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 5},
                        sm = {'size': 5, 'order': 4},
                        md = {'size': 2, 'order': 4},
                        lg = {'size': 2, 'order': 4},
                        xl = {'size': 2, 'order': 5},
                    ),

                    # Rate limit column
                    dbc.Col([
                        html.H6(
                            'Caudal límite',
                            className = 'control-title'
                        ),
                        
                        dcc.Input(
                            id = 'gas-dca-auto-forecast-q-lim-input',
                            type = 'number',
                            placeholder = 'm3/d',
                            value = 1,
                            debounce = True,
                            max = 100,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 6},
                        sm = {'size': 5, 'order': 6},
                        md = {'size': 2, 'order': 6},
                        lg = {'size': 2, 'order': 6},
                        xl = {'size': 2, 'order': 6},
                    )],
                ),
                
                # Fix last rate toggle
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            daq.ToggleSwitch(
                                id = 'gas-fix-last-q',
                                size = 35,
                                value = False,
                                className = 'toggle-switch',
                            ),

                            html.H6(
                                'Fijar pronóstico a último caudal',
                                className = 'control-title',
                            ),],
                            className = 'control-div-row'
                        ),],
                        className = 'control-div',
                        width = 12,
                    )],
                ),
                
                # Frac stages normalization
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            daq.ToggleSwitch(
                                id = 'gas-frac-stages-norm',
                                size = 35,
                                value = False,
                                className = 'toggle-switch',
                            ),

                            html.H6(
                                'Normalizar por etapas de fractura',
                                className = 'control-title',
                            ),],
                            className = 'control-div-row'
                        ),],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 1},
                        sm = {'size': 12, 'order': 1},
                        md = {'size': 5, 'order': 1},
                        lg = {'size': 4, 'order': 1},
                        xl = {'size': 3, 'order': 1},
                    ),

                    dbc.Col([
                        dcc.Input(
                            id = 'gas-frac-stages-norm-input',
                            type = 'number',
                            placeholder = 'Num de etapas',
                            value = 30,
                            min = 1,
                            max = 200,
                            debounce = True,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 2},
                        sm = {'size': 6, 'order': 2},
                        md = {'size': 2, 'order': 2},
                        lg = {'size': 2, 'order': 2},
                        xl = {'size': 1, 'order': 2},
                    )],
                ),
                
                # Frac lateral length normalization
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            daq.ToggleSwitch(
                                id = 'gas-frac-latlen-norm',
                                size = 35,
                                value = False,
                                className = 'toggle-switch',
                            ),

                            html.H6(
                                'Normalizar por rama lateral',
                                className = 'control-title',
                            ),],
                            className = 'control-div-row'
                        ),],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 1},
                        sm = {'size': 12, 'order': 1},
                        md = {'size': 5, 'order': 1},
                        lg = {'size': 4, 'order': 1},
                        xl = {'size': 3, 'order': 1},
                    ),

                    dbc.Col([
                        dcc.Input(
                            id = 'gas-frac-latlen-norm-input',
                            type = 'number',
                            placeholder = 'm',
                            value = 2500,
                            min = 1,
                            max = 9999,
                            debounce = True,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 2},
                        sm = {'size': 6, 'order': 2},
                        md = {'size': 2, 'order': 2},
                        lg = {'size': 2, 'order': 2},
                        xl = {'size': 1, 'order': 2},
                    )],
                ),
                
                # GOR control row
                dbc.Row([
                    # GOR method column
                    dbc.Col([
                        html.H6(
                            'Pronóstico de GOR',
                            className = 'control-title'
                        ),

                        dcc.Dropdown(
                            id = 'gas-dca-auto-GOR-method',
                            options = [
                                {'label': 'Automático', 'value': 'GOR_AUTO'},
                                {'label': 'Manual', 'value': 'GOR_MANUAL'}
                            ],
                            multi = False,
                            value = 'GOR_AUTO',
                            clearable = False,
                            searchable = False,
                            className = 'dropdown-control',
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 1},
                        sm = {'size': 12, 'order': 1},
                        md = {'size': 5, 'order': 1},
                        lg = {'size': 4, 'order': 1},
                        xl = {'size': 3, 'order': 1},
                    ),
                    
                    # GORi column
                    dbc.Col([
                        html.H6(
                            'GORi',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-auto-GORi',
                                type = 'number',
                                placeholder = 'm3/m3',
                                value = 100,
                                min = 0,
                                max = 100_000,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 2},
                        sm = {'size': 6, 'order': 2},
                        md = {'size': 2, 'order': 2},
                        lg = {'size': 2, 'order': 2},
                        xl = {'size': 1, 'order': 2},
                    ),
                    
                    # Gp@Pb column
                    dbc.Col([
                        html.H6(
                            'Gp@Pb',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-auto-Gp-pb',
                                type = 'number',
                                placeholder = 'Mm3',
                                value = 20000,
                                min = 0,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 3},
                        sm = {'size': 6, 'order': 3},
                        md = {'size': 2, 'order': 3},
                        lg = {'size': 2, 'order': 3},
                        xl = {'size': 1, 'order': 3},
                    ),

                    # GORmax column
                    dbc.Col([
                        html.H6(
                            'GORmax',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-auto-GORmax',
                                type = 'number',
                                placeholder = 'm3/m3',
                                value = 500,
                                min = 0,
                                max = 100_000,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 4},
                        sm = {'size': 6, 'order': 4},
                        md = {'size': 2, 'order': 5},
                        lg = {'size': 2, 'order': 4},
                        xl = {'size': 1, 'order': 4},
                    ),

                    # Gp@GORmax column
                    dbc.Col([
                        html.H6(
                            'Gp@GORmax',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-auto-Gp-GORmax',
                                type = 'number',
                                placeholder = 'Mm3',
                                value = 30000,
                                min = 0,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 5},
                        sm = {'size': 6, 'order': 5},
                        md = {'size': 2, 'order': 6},
                        lg = {'size': 2, 'order': 5},
                        xl = {'size': 1, 'order': 5},
                    ),

                    # GORf column
                    dbc.Col([
                        html.H6(
                            'GORf',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-auto-GORf',
                                type = 'number',
                                placeholder = 'm3/m3',
                                value = 200,
                                min = 0,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 6},
                        sm = {'size': 6, 'order': 6},
                        md = {'size': 2, 'order': 7},
                        lg = {'size': 2, 'order': 7},
                        xl = {'size': 1, 'order': 6},
                    ),

                    # Gp@GORf column
                    dbc.Col([
                        html.H6(
                            'Gp@GORf',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-auto-Gp-GORf',
                                type = 'number',
                                placeholder = 'Mm3',
                                value = 40000,
                                min = 0,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 7},
                        sm = {'size': 6, 'order': 7},
                        md = {'size': 2, 'order': 8},
                        lg = {'size': 2, 'order': 8},
                        xl = {'size': 1, 'order': 7},
                    ),

                    # a column
                    dbc.Col([
                        html.Div([
                            html.H6(
                                'a [1-20]',
                                className = 'control-title'
                            ),

                            html.Img(
                                id = 'gas-dca-auto-a-tooltip',
                                src = '/assets/question.png',
                                className = 'control-icon',
                            ),

                            dbc.Tooltip(
                                "Parámetro relacionado con la curvatura hasta el GOR max",
                                target = "gas-dca-auto-a-tooltip",
                            )],
                            className = 'div-flex-row',
                        ),
                    
                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-auto-GOR-a',
                                type = 'number',
                                placeholder = '',
                                value = 5,
                                min = 1,
                                max = 20,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 8},
                        sm = {'size': 12, 'order': 8},
                        md = {'size': 2, 'order': 9},
                        lg = {'size': 2, 'order': 9},
                        xl = {'size': 1, 'order': 8},
                    ),
                    
                    # Empty column
                    dbc.Col([],
                        className = 'control-div',
                        xs = {'size': 1, 'order': 9},
                        sm = {'size': 1, 'order': 9},
                        md = {'size': 3, 'order': 4},
                        lg = {'size': 4, 'order': 6},
                        xl = {'size': 1, 'order': 9},
                    ),]
                )],
            )],
            
            id = 'gas-dca-auto-controls',
            is_open = False,
        ),

        #----------------------------------------
        # DCA manual controls
        #----------------------------------------
        dbc.Collapse([
            dbc.Card([
                dbc.CardHeader([
                    html.H4(
                        'Declinación manual',
                        className = 'card-title'
                    )]
                ),

                dbc.Row([
                    # Decline model column
                    dbc.Col([
                        html.H6(
                            'Modelo de declinación',
                            className = 'control-title'
                        ),
                        
                        dcc.Dropdown(
                            id = 'gas-dca-manual-model',
                            options = [
                                {'label': 'Hiperbólico', 'value': 'HYP'},
                                {'label': 'Hiperbólico modificado', 'value': 'HM'}
                            ],
                            multi = False,
                            value = 'HYP',
                            clearable = False,
                            searchable = False,
                            className = 'dropdown-control',
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 1},
                        sm = {'size': 12, 'order': 1},
                        md = {'size': 5, 'order': 1},
                        lg = {'size': 5, 'order': 1},
                        xl = {'size': 3, 'order': 1},
                    ),

                    # Exponential change column
                    dbc.Col([
                        html.H6(
                            'Cambio a exponencial',
                            className = 'control-title'
                        ),
                        
                        dcc.Dropdown(
                            id = 'gas-dca-manual-exp-start-method',
                            options = [
                                {'label': 'Por tiempo (días)', 'value': 'EXP_START_TIME'},
                                {'label': 'Por declinación (%/año)', 'value': 'EXP_START_DT'}
                            ],
                            multi = False,
                            value = 'EXP_START_DT',
                            clearable = False,
                            searchable = False,
                            className = 'dropdown-control',
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 2},
                        sm = {'size': 10, 'order': 2},
                        md = {'size': 5, 'order': 2},
                        lg = {'size': 5, 'order': 2},
                        xl = {'size': 2, 'order': 2},
                    ),

                    # Exponential change input column
                    dbc.Col([
                        dcc.Input(
                            id = 'gas-dca-manual-exp-start-input',
                            type = 'number',
                            placeholder = 'D anual',
                            value = 10,
                            debounce = True,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 3},
                        sm = {'size': 2, 'order': 3},
                        md = {'size': 2, 'order': 3},
                        lg = {'size': 2, 'order': 3},
                        xl = {'size': 1, 'order': 3},
                    ),

                    # Empty column
                    dbc.Col([],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 4},
                        sm = {'size': 1, 'order': 5},
                        md = {'size': 3, 'order': 5},
                        lg = {'size': 3, 'order': 5},
                        xl = {'size': 1, 'order': 4},
                    ),

                    # Years to forecast column
                    dbc.Col([
                        html.H6(
                            'Años a pronosticar',
                            className = 'control-title'
                        ),
                        
                        dcc.Input(
                            id = 'gas-dca-manual-forecast-end-time-input',
                            type = 'number',
                            placeholder = 'años',
                            value = 35,
                            debounce = True,
                            max = 50,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 5},
                        sm = {'size': 5, 'order': 4},
                        md = {'size': 2, 'order': 4},
                        lg = {'size': 2, 'order': 4},
                        xl = {'size': 2, 'order': 5},
                    ),

                    # Rate limit column
                    dbc.Col([
                        html.H6(
                            'Caudal límite',
                            className = 'control-title'
                        ),
                        
                        dcc.Input(
                            id = 'gas-dca-manual-forecast-q-lim-input',
                            type = 'number',
                            placeholder = 'Mm3/d',
                            value = 1,
                            debounce = True,
                            max = 100,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 6},
                        sm = {'size': 5, 'order': 6},
                        md = {'size': 2, 'order': 6},
                        lg = {'size': 2, 'order': 6},
                        xl = {'size': 2, 'order': 6},
                    )]
                ),
                
                dbc.Row([
                    # Forecast name column
                    dbc.Col([
                        html.H6(
                            'Nombre del pronóstico',
                            className = 'control-title'
                        ),

                        dcc.Input(
                            id = 'gas-synth-wellname',
                            type = 'text',
                            debounce = True,
                            pattern = '[^_ \s]+',
                            className = 'control-input-wide',
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 1},
                        sm = {'size': 12, 'order': 1},
                        md = {'size': 5, 'order': 1},
                        lg = {'size': 5, 'order': 1},
                        xl = {'size': 3, 'order': 1},
                    ),

                    dbc.Col([
                        html.H6(
                            'Fecha inicio pronóstico',
                            className = 'control-title'
                        ),

                        dcc.DatePickerSingle(
                            id = 'gas-synth-date-picker',
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
                    )],
                ),
                
                dbc.Row([
                    # Peak rate column
                    dbc.Col([
                        html.H6(
                            'Caudal pico [Mm3/d]',
                            className = 'control-title'
                        ),

                        dcc.Input(
                            id = 'gas-qi-input',
                            type = 'number',
                            placeholder = 'Mm3/d',
                            value = 100,
                            debounce = True,
                            max = 1000,
                            className = 'control-input',
                        ),],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 1},
                        sm = {'size': 6, 'order': 1},
                        md = {'size': 5, 'order': 1},
                        lg = {'size': 3, 'order': 1},
                        xl = {'size': 3, 'order': 1},
                    ),

                    # Peak time column
                    dbc.Col([
                        html.H6(
                            'Tiempo al pico [d]',
                            className = 'control-title'
                        ),

                        dcc.Input(
                            id = 'gas-ti-input',
                            type = 'number',
                            placeholder = 'días',
                            value = 90,
                            debounce = True,
                            min = 1,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 2},
                        sm = {'size': 6, 'order': 2},
                        md = {'size': 5, 'order': 2},
                        lg = {'size': 3, 'order': 2},
                        xl = {'size': 3, 'order': 2},
                    ),
                    
                    # B parameter column
                    dbc.Col([
                        html.H6(
                            'Parámetro b',
                            className = 'control-title'
                        ),

                        dcc.Input(
                            id = 'gas-b-input',
                            type = 'number',
                            placeholder = '',
                            value = 1.2,
                            debounce = True,
                            max = 4,
                            min = 0,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 3},
                        sm = {'size': 6, 'order': 3},
                        md = {'size': 5, 'order': 3},
                        lg = {'size': 3, 'order': 3},
                        xl = {'size': 3, 'order': 3},
                    ),

                    # Di parameter column
                    dbc.Col([
                        html.H6(
                            'Parámetro Di [% 1/yr]',
                            className = 'control-title'
                        ),

                        dcc.Input(
                            id = 'gas-d-input',
                            type = 'number',
                            placeholder = '% 1/yr',
                            value = 100,
                            debounce = True,
                            max = 500,
                            min = 0.01,
                            className = 'control-input',
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 4},
                        sm = {'size': 6, 'order': 4},
                        md = {'size': 5, 'order': 4},
                        lg = {'size': 3, 'order': 4},
                        xl = {'size': 3, 'order': 4},
                    )],
                ),
                
                dbc.Row([
                    # GOR method column
                    dbc.Col([
                        html.H6(
                            'Pronóstico de GOR',
                            className = 'control-title'
                        ),

                        dcc.Dropdown(
                            id = 'gas-dca-manual-GOR-method',
                            options = [
                                {'label': 'Manual', 'value': 'GOR_MANUAL'}
                            ],
                            multi = False,
                            value = 'GOR_MANUAL',
                            clearable = False,
                            searchable = False,
                            className = 'dropdown-control',
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 1},
                        sm = {'size': 12, 'order': 1},
                        md = {'size': 5, 'order': 1},
                        lg = {'size': 4, 'order': 1},
                        xl = {'size': 3, 'order': 1},
                    ),
                    
                    # GORi column
                    dbc.Col([
                        html.H6(
                            'GORi',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-manual-GORi',
                                type = 'number',
                                placeholder = 'm3/m3',
                                value = 100,
                                min = 0,
                                max = 100_000,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 2},
                        sm = {'size': 6, 'order': 2},
                        md = {'size': 2, 'order': 2},
                        lg = {'size': 2, 'order': 2},
                        xl = {'size': 1, 'order': 2},
                    ),

                    # Gp@Pb column
                    dbc.Col([
                        html.H6(
                            'Gp@Pb',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-manual-Gp-pb',
                                type = 'number',
                                placeholder = 'Mm3',
                                value = 20000,
                                min = 0,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 3},
                        sm = {'size': 6, 'order': 3},
                        md = {'size': 2, 'order': 3},
                        lg = {'size': 2, 'order': 3},
                        xl = {'size': 1, 'order': 3},
                    ),

                    # GORmax column
                    dbc.Col([
                        html.H6(
                            'GORmax',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-manual-GORmax',
                                type = 'number',
                                placeholder = 'm3/m3',
                                value = 500,
                                min = 0,
                                max = 100_000,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 4},
                        sm = {'size': 6, 'order': 4},
                        md = {'size': 2, 'order': 5},
                        lg = {'size': 2, 'order': 4},
                        xl = {'size': 1, 'order': 4},
                    ),

                    # Gp@GORmax column
                    dbc.Col([
                        html.H6(
                            'Gp@GORmax',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-manual-Gp-GORmax',
                                type = 'number',
                                placeholder = 'Mm3',
                                value = 30000,
                                min = 0,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 5},
                        sm = {'size': 6, 'order': 5},
                        md = {'size': 2, 'order': 6},
                        lg = {'size': 2, 'order': 5},
                        xl = {'size': 1, 'order': 5},
                    ),

                    # GORf column
                    dbc.Col([
                        html.H6(
                            'GORf',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-manual-GORf',
                                type = 'number',
                                placeholder = 'Mm3',
                                value = 200,
                                min = 0,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 6},
                        sm = {'size': 6, 'order': 6},
                        md = {'size': 2, 'order': 7},
                        lg = {'size': 2, 'order': 7},
                        xl = {'size': 1, 'order': 6},
                    ),

                    # Gp@GORf column
                    dbc.Col([
                        html.H6(
                            'Gp@GORf',
                            className = 'control-title'
                        ),

                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-manual-Gp-GORf',
                                type = 'number',
                                placeholder = 'Mm3',
                                value = 40000,
                                min = 0,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 6, 'order': 7},
                        sm = {'size': 6, 'order': 7},
                        md = {'size': 2, 'order': 8},
                        lg = {'size': 2, 'order': 8},
                        xl = {'size': 1, 'order': 7},
                    ),

                    # a column
                    dbc.Col([
                        html.Div([
                            html.H6(
                                'a [1-20]',
                                className = 'control-title'
                            ),

                            html.Img(
                                id = 'gas-dca-manual-a-tooltip',
                                src = '/assets/question.png',
                                className = 'control-icon',
                            ),

                            dbc.Tooltip(
                                "Parámetro relacionado con la curvatura hasta el GOR max",
                                target = "gas-dca-manual-a-tooltip",
                            )],
                            className = 'div-flex-row',
                        ),
                    
                        html.Div([
                            dcc.Input(
                                id = 'gas-dca-manual-GOR-a',
                                type = 'number',
                                placeholder = '',
                                value = 5,
                                min = 1,
                                max = 20,
                                debounce = True,
                                className = 'control-input',
                            )],
                        )],
                        className = 'control-div',
                        xs = {'size': 12, 'order': 8},
                        sm = {'size': 12, 'order': 8},
                        md = {'size': 2, 'order': 9},
                        lg = {'size': 2, 'order': 9},
                        xl = {'size': 1, 'order': 8},
                    ),
                    
                    # Empty column
                    dbc.Col([],
                        className = 'control-div',
                        xs = {'size': 1, 'order': 9},
                        sm = {'size': 1, 'order': 9},
                        md = {'size': 3, 'order': 4},
                        lg = {'size': 4, 'order': 6},
                        xl = {'size': 1, 'order': 9},
                    )]
                )],
            )],
            
            id = 'gas-dca-manual-controls',
            is_open = False,
        ),

        #----------------------------------------
        # Decline curves
        #----------------------------------------
        dbc.Card([
            dbc.CardHeader([
                html.H4('Curvas de declinación', className='card-title'),

                html.Img(
                    src = 'assets/exclamation.png',
                    id = 'gas-forecasts-warning',
                    style = {'height': '18px', 'margin': '0px 15px 0px 15px'},
                ),

                dbc.Tooltip(
                    'Declinación automática calculada sobre qg vs Gp, pues no se cuenta con datos de presión',
                    target = "gas-forecasts-warning",
                ),],
                className = 'div-flex-row'
            ),

            #----------------------------------------
            # Graph toggle control
            #----------------------------------------
            html.Div([
                html.H6('Lineal', className = 'control-title'),

                daq.ToggleSwitch(
                    id = 'gas-fc-log-scale',
                    size = 35,
                    value = True,
                    className = 'toggle-switch',
                ),

                html.H6('Log', className = 'control-title')],
                className = 'toggle-scale'
            ),

            #----------------------------------------
            # Graphs tabs
            #----------------------------------------
            dbc.Tabs([
                # qg tab
                dbc.Tab([
                    dcc.Loading(
                        children = [dcc.Graph(id = 'gas-qg-vs-tdp')],
                        type = 'dot',
                        color = '#2A5261',
                        fullscreen = False
                    ),
                    
                    # My forecast qg
                    dbc.Collapse([
                        dcc.Loading(
                            children = [dcc.Graph(id = 'gas-qg-vs-tdp_db')],
                            type = 'dot',
                            color = '#2A5261',
                            fullscreen = False
                        )],
                        id = 'gas-qg-tdp-db-forecast-container',
                        is_open = False,
                    )],

                    label = 'qg vs t'
                ),

                # qg vs Gp tab
                dbc.Tab([
                    dcc.Loading(
                        children = [dcc.Graph(id = 'gas-qg-vs-gp')],
                        type = 'dot',
                        color = '#2A5261',
                        fullscreen = False
                    ),
                    
                    # My forecast qg
                    dbc.Collapse([
                        dcc.Loading(
                            children = [dcc.Graph(id = 'gas-qg-vs-gp_db')],
                            type = 'dot',
                            color = '#2A5261',
                            fullscreen = False
                        )],
                        id = 'gas-qg-gp-db-forecast-container',
                        is_open = False,
                    )],

                    label = 'qg vs Gp'
                ),

                # Gp tab      
                dbc.Tab([
                    dcc.Loading(
                        children = [dcc.Graph(id = 'gas-gp-vs-tdp')],
                        type = 'dot',
                        color = '#2A5261',
                        fullscreen = False
                    ),
                    
                    # My forecast Gp
                    dbc.Collapse([
                        dcc.Loading(
                            children = [dcc.Graph(id = 'gas-gp-vs-tdp_db')],
                            type = 'dot',
                            color = '#2A5261',
                            fullscreen = False
                        )],

                        id = 'gas-gp-tdp-db-forecast-container',
                        is_open = False,
                    )],
                    label = 'Gp vs t'
                ),

                # GOR tab
                dbc.Tab([
                    dcc.Loading(
                        children = [dcc.Graph(id = 'gas-gor-vs-gp')],
                        type = 'dot',
                        color = '#2A5261',
                        fullscreen = False
                    ),
                    
                    # My forecast GOR
                    dbc.Collapse([
                        dcc.Loading(
                            children = [dcc.Graph(id = 'gas-gor-vs-gp_db')],
                            type = 'dot',
                            color = '#2A5261',
                            fullscreen = False
                        )],
                        id = 'gas-GOR-gp-db-forecast-container',
                        is_open = False,
                    )],

                    label = 'GOR vs Gp'
                ),
                        
                # GOR tab
                dbc.Tab([
                    dcc.Loading(
                        children = [dcc.Graph(id = 'gas-gor-vs-tdp')],
                        type = 'dot',
                        color = '#2A5261',
                        fullscreen = False
                    ),
                    
                    # My forecast GOR
                    dbc.Collapse([
                        dcc.Loading(
                            children = [dcc.Graph(id = 'gas-gor-vs-tdp_db')],
                            type = 'dot',
                            color = '#2A5261',
                            fullscreen = False
                        )],
                        id = 'gas-GOR-tdp-db-forecast-container',
                        is_open = False,
                    )],
                    label = 'GOR vs t'
                ),
                
                # qo tab
                dbc.Tab([
                    dcc.Loading(
                        children = [dcc.Graph(id = 'gas-qo-vs-tdp')],
                        type = 'dot',
                        color = '#2A5261',
                        fullscreen = False
                    ),
                    
                    # My forecast qo
                    dbc.Collapse([
                        dcc.Loading(
                            children = [dcc.Graph(id = 'gas-qo-vs-tdp_db')],
                            type = 'dot',
                            color = '#2A5261',
                            fullscreen = False
                        )],
                        id = 'gas-qo-tdp-db-forecast-container',
                        is_open = False,
                    )],

                    label = 'qo vs t'
                ),

                # Np tab
                dbc.Tab([
                    dcc.Loading(
                        children = [dcc.Graph(id = 'gas-np-vs-tdp')],
                        type = 'dot',
                        color = '#2A5261',
                        fullscreen = False
                    ),
                    
                    # My forecast Np
                    dbc.Collapse([
                        dcc.Loading(
                            children = [dcc.Graph(id = 'gas-np-vs-tdp_db')],
                            type = 'dot',
                            color = '#2A5261',
                            fullscreen = False
                        )],
                        id = 'gas-np-tdp-db-forecast-container',
                        is_open = False,
                    )],

                    label = 'Np vs t'
                ),
                ]
            )]
        ),

        #----------------------------------------
        # Wells info table
        #----------------------------------------
        dbc.Collapse([
            dbc.Card([
                dbc.CardHeader([
                    html.H4(
                        'Información de pozos seleccionados',
                        className = 'card-title'
                    ),
                    html.Button([
                        'Exportar a xlsx'],
                        className = 'control-btn',
                        id = 'gas-export-wells-info',
                        **{'data-dummy': ''}
                    )],
                    className = 'filter-row',
                ),

                dt.DataTable(
                id = 'gas-wells-info-table',
                columns = [
                    {'name': 'Pozo:Form', 'id': 'Pozo_Form_P'},
                    {'name': 'MinFecha', 'id': 'MinFecha'},
                    {'name': 'Np\n[m3]', 'id': 'Np'},
                    {'name': 'Gp\n[Mm3]', 'id': 'Gp'},
                    {'name': 'Fracturas', 'id': 'Fracturas'},
                    {'name': 'Rama\n[m]', 'id': 'Rama'},
                    {'name': 'qo_ef_peak\n[m3/d]', 'id': 'qo_ef_peak'},
                    {'name': 'qg_ef_peak\n[Mm3/d]', 'id': 'qg_ef_peak'},
                    {'name': 'qo_avg\n[m3/d]', 'id': 'qo_avg'},
                    {'name': 'qg_avg\n[Mm3/d]', 'id': 'qg_avg'},
                    {'name': 'Agente sostén\n[lb/ft]', 'id': 'proppant'},
                    {'name': 'Agua inyectada\n[Kbbl]', 'id': 'water_inj'}
                ],
                style_header = {'fontWeight': 'bold'},
                style_cell = {'whiteSpace': 'pre-line'},
                style_table = {'overflowX': 'scroll'},
                filter_action = 'native',
                page_size = 10,
                export_format = 'xlsx',
                )]
            )],
            id = 'gas-wells-info-container',
            is_open = False
        ),

        #----------------------------------------
        # Forecasts EUR data table row
        #----------------------------------------
        dbc.Collapse([
            dbc.Card([
                dbc.CardHeader([
                    html.H4('Información de pronósticos', className = 'card-title'),

                    html.Button(
                        'Exportar a xlsx',
                        id = 'gas-export-wells-eur',
                        className = 'control-btn',
                        **{'data-dummy': ''}
                    )],
                    className = 'filter-row',
                ),

                # DataTable forecasts EUR
                dt.DataTable(
                    id = 'gas-EUR-forecasts-table',
                    columns = [
                        {'name': 'Pozo:Form', 'id': 'Pozo_Form_P'},
                        {'name': 'b', 'id': 'b'},
                        {'name': 'Di (hyp)\n[% 1/yr]', 'id': 'd_hyp'},
                        {'name': 'Di (exp)\n[% 1/yr]', 'id': 'd_exp'},
                        {'name': 'Etapas fractura', 'id': 'Fracturas'},
                        {'name': 'Etapas fractura\n(normaliz)', 'id': 'Frac_norm'},
                        {'name': 'Rama lateral\n[m]', 'id': 'Rama'},
                        {'name': 'Rama lateral\n(normaliz) [m]', 'id': 'Rama_norm'},
                        {'name': 'EUR oil\n[m3]', 'id': 'EUR_oil'},
                        {'name': 'EUR oil\n[Kbbl]', 'id': 'EUR_oil_bbl'},
                        {'name': 'EUR_oil/etapas\n[Kbbl/etapa]', 'id': 'EUR_oil_fracs'},
                        {'name': 'EUR_oil/rama_lat\n[Kbbl/m]', 'id': 'EUR_oil_ll'},
                        {'name': 'EUR gas\n[Mm3]', 'id': 'EUR_gas'},
                        {'name': 'EUR gas\n[MMscf]', 'id': 'EUR_gas_scf'},
                        {'name': 'EUR_gas/etapas\n[MMscf/etapa]', 'id': 'EUR_gas_fracs'}
                    ],
                    style_header = {'fontWeight': 'bold'},
                    style_cell = {'whiteSpace': 'pre-line'},
                    style_table = {'overflowX': 'scroll'},
                    filter_action = 'native',
                    page_size = 10,
                    export_format = 'xlsx',
                ),
            ]
            )],

            id = 'gas-dca-EUR-container',
            is_open = False,
        ),

        #----------------------------------------
        # History + forecasts data table row
        #----------------------------------------
        dbc.Card([
            dbc.CardHeader([
                html.H4('Historia + pronósticos', className = 'card-title'),
                html.Button(
                    'Exportar a xlsx',
                    id = 'gas-export-forecast',
                    className = 'control-btn',
                )],
                className = 'filter-row',
            ),

            # DataTable with history + forecast
            dt.DataTable(
                id = 'gas-history-forecasts-table',
                columns = [
                    {'name': 'Pozo:Form', 'id': 'Pozo_Form_P'},
                    {'name': 'TdP\n[d]', 'id': 'TdP'},
                    {'name': 'qo\n[m3/d]', 'id': 'qo'},
                    {'name': 'Np\n[m3]', 'id': 'Np'},
                    {'name': 'GOR\n[m3/m3]', 'id': 'GOR'},
                    {'name': 'qg\n[Mm3/d]', 'id': 'qg'},
                    {'name': 'Gp\n[Mm3]', 'id': 'Gp'},
                ],
                style_header = {'fontWeight': 'bold'},
                style_table = {'overflowX': 'scroll'},
                style_cell = {'whiteSpace': 'pre-line'},
                filter_action = 'native',
                page_size = 15,
                export_format = 'xlsx',
            ),
        ]),

        common_components.footer,
    ],

    id = 'gas-container',
    className = 'left-expanded',
    fluid = True
    )
])


#------------------------------------------------------------------------------
# Callbacks
#------------------------------------------------------------------------------
@app.callback(
    [Output("gas-latlength-input-start", "value"),
    Output("gas-latlength-input-end", "value"),
    Output("gas-latlength-slider", "value"),
    Output("gas-fracs-input-start", "value"),
    Output("gas-fracs-input-end", "value"),
    Output("gas-fracs-slider", "value")],

    [Input("gas-latlength-input-start", "value"),
    Input("gas-latlength-input-end", "value"),
    Input("gas-latlength-slider", "value"),
    Input("gas-latlength-clear", "n_clicks"),
    Input("gas-fracs-input-start", "value"),
    Input("gas-fracs-input-end", "value"),
    Input("gas-fracs-slider", "value"),
    Input("gas-fracs-clear", "n_clicks")]
)
def update_sliders_inputs(latlen_start, latlen_end, latlen_slider, latlen_clear,
    fracs_start, fracs_end, fracs_slider, fracs_clear):
    '''
    Keeps the lateral length and fractures inputs and sliders updated. If the
    user changes an input the slider is updated, and viceversa.
    Also controls clearing inputs/sliders after clear button click.

    Params:
        - latlen_start (float | None): lateral length initial value
        - latlen_end (float | None): lateral length final value
        - latlen_slider (list of float | None): if provided, length 2 list with
            the following elements:
            [lateral length initial value, lateral length final value]
        - latlen_clear (int): number of clicks on lateral length clear button
        - fracs_start (float | None): fractures initial value
        - fracs_end (float | None): fractures final value
        - fracs_slider (list of float | None): if provided, length 2 list with
            the following elements:
            [fractures initial value, fractures final value]
        - fracs_clear (int): number of clicks on fractures clear button

    Returns:
        - latlen_start (float | None): lateral length initial value
        - latlen_end (float | None): lateral length final value
        - latlen_slider (list of float | None): if provided, length 2 list with
            the following elements:
            [lateral length initial value, lateral length final value]
        - fracs_start (float | None): fractures initial value
        - fracs_end (float | None): fractures final value
        - fracs_slider (list of float | None): if provided, length 2 list with
            the following elements:
            [fractures initial value, fractures final value]
    
    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    def update_single_slider(start, end, slider):
        '''
        Updates the inputs and slider depending on which element has triggered
        the callback.

        Params:
            - start (float | None): input initial value
            - end (float | None): input final value
            - slider (list of float | None): if provided, length 2 list with
                the following elements:
                [input initial value, input final value]

        Returns:
            - start (float | None): input initial value
            - end (float | None): input final value
            - slider (list of float | None): if provided, length 2 list with
                the following elements:
                [input initial value, input final value]

        Ariel Cabello (acabello@fdc-group.com) - May 2022
        '''

        if slider is None: return start, end, slider

        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if 'start' in trigger_id:
            start = start
        else:
            start = slider[0]
        
        if 'end' in trigger_id:
            end = end
        else:
            end = slider[1]
        
        if 'slider' in trigger_id:
            slider = slider
        else:
            slider = [start, end]
        
        return start, end, slider

    # Clear dropdowns if button clicked
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if latlen_clear and 'latlength-clear' in trigger_id:
        latlen_start, latlen_end, latlen_slider = None, None, None

    if fracs_clear and 'fracs-clear' in trigger_id:
        fracs_start, fracs_end, fracs_slider = None, None, None

    # Update valus
    latlen_start, latlen_end, latlen_slider = update_single_slider(
        latlen_start, latlen_end, latlen_slider)
    
    fracs_start, fracs_end, fracs_slider = update_single_slider(
        fracs_start, fracs_end, fracs_slider)

    return (latlen_start, latlen_end, latlen_slider, fracs_start, fracs_end,
        fracs_slider)


@app.callback(
    [Output('gas-date-picker', 'start_date'),
    Output('gas-date-picker', 'end_date')],

    Input('gas-datepicker-clear', 'n_clicks')
)
def clear_datepicker(click):
    '''
    Clears date picker start_date and end_date when clear button is clicked.

    Params:
        - click (None | int): number of clicks on date picker clear button

    Returns:
        - start_date (None): None after button is clicked
        - end_date (None): None after button is clicked

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''
    
    return None, None


@app.callback(
    [Output('gas-btn-decline-auto', 'className'),
    # Output('gas-btn-decline-manual', 'className'),
    Output('gas-btn-forecasts-from-db', 'className')],

    [Input('gas-btn-decline-auto', 'n_clicks'),
    # Input('gas-btn-decline-manual', 'n_clicks'),
    Input('gas-btn-forecasts-from-db', 'n_clicks')],

    [State('gas-btn-decline-auto', 'className'),
    # State('gas-btn-decline-manual', 'className'),
    State('gas-btn-forecasts-from-db', 'className')]
)
def toggle_ribbon_btns(_1, _2, auto_className, fc_from_db_className):
    '''
    TODO: COMPLETAR DOCSTRING
    
    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if 'auto' in trigger_id:
        if 'pressed' in auto_className:
            return 'ribbon-btn', fc_from_db_className
        else:
            return 'ribbon-btn-pressed', fc_from_db_className
    
    if 'from-db' in trigger_id:
        if 'pressed' in fc_from_db_className:
            return auto_className, 'ribbon-btn'
        else:
            return auto_className, 'ribbon-btn-pressed'

    return auto_className, fc_from_db_className


@app.callback(
    [Output('gas-geometry-container', 'label'),
    Output('gas-formation-container', 'label'),
    Output('gas-field-container', 'label'),
    Output('gas-wells-container', 'label')],

    [Input('gas-geometry-dropdown', 'value'),
    Input('gas-geometry-dropdown', 'options'),
    Input('gas-formation-dropdown', 'value'),
    Input('gas-formation-dropdown', 'options'),
    Input('gas-field-dropdown', 'value'),
    Input('gas-field-dropdown', 'options'),
    Input('gas-wells-dropdown', 'value'),
    Input('gas-wells-dropdown', 'options')]
)
def update_dropdowns_labels(geom_val, geom_opt, form_val, form_opt, field_val,
    field_opt, wells_val, wells_opt):
    '''
    TODO: COMPLETAR DOCSTRING
    
    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''
    
    def count_elements(dropdown):
        if dropdown[0] is None:
            return 0
        elif 'ALL' in dropdown[0]:
            return f'Todos ({len(dropdown[1]) - 1})'
        else:
            return len(dropdown[0])
    
    values = [geom_val, form_val, field_val, wells_val]
    options = [geom_opt, form_opt, field_opt, wells_opt]
    
    return [str(count_elements(dropdown)) + ' seleccionados'
        for dropdown in zip(values, options)]
    

@app.callback(
    [Output('gas-geometry-dropdown', 'options'),
    Output('gas-geometry-dropdown', 'value'),
    Output('gas-formation-dropdown', 'options'),
    Output('gas-formation-dropdown', 'value'),
    Output('gas-field-dropdown', 'options'),
    Output('gas-field-dropdown', 'value'),
    Output('gas-wells-dropdown', 'options'),
    Output('gas-wells-dropdown', 'value'),
    Output('gas-user-selection', 'data'),
    Output('gas-latlength-input-start', 'min'),
    Output('gas-latlength-input-start', 'max'),
    Output('gas-latlength-input-end', 'min'),
    Output('gas-latlength-input-end', 'max'),
    Output('gas-latlength-slider', 'min'),
    Output('gas-latlength-slider', 'max'),
    Output('gas-fracs-input-start', 'min'),
    Output('gas-fracs-input-start', 'max'),
    Output('gas-fracs-input-end', 'min'),
    Output('gas-fracs-input-end', 'max'),
    Output('gas-fracs-slider', 'min'),
    Output('gas-fracs-slider', 'max'),
    Output('gas-select-all-warning', 'className')],

    [Input('gas-date-picker', 'start_date'),
    Input('gas-date-picker', 'end_date'),
    Input('gas-geometry-dropdown', 'value'),
    Input('gas-geometry-clear', 'n_clicks'),
    Input('gas-formation-dropdown', 'value'),
    Input('gas-formation-clear', 'n_clicks'),
    Input('gas-field-dropdown', 'value'),
    Input('gas-field-clear', 'n_clicks'),
    Input('gas-latlength-input-start', 'value'),
    Input('gas-latlength-input-end', 'value'),
    Input('gas-fracs-input-start', 'value'),
    Input('gas-fracs-input-end', 'value'),
    Input('gas-wells-clear', 'n_clicks')],

    [State('gas-user-selection', 'data'),
    State('gas-wells-dropdown', 'value')]
)
def update_dropdowns(start_date, end_date, geometry, geom_clear, formation,
    form_clear, field, field_clear, latlen_start, latlen_end, fracs_start,
    fracs_end, wells_clear, previous, selected_wells):
    '''
    Updates select wells dropdown based on date picker, geometry, formation,
    company/field and lateral length selection.

    TODO: COMPLETAR DOCSTRING

    Params:
        - start_date (str | None): formated as YYYY-MM-DD
        - end_date (str | None): formated as YYYY-MM-DD
        - geometry
        - formation
        - field
        - previous

    Returns:
        - geometry_dropdown
        - formation_dropdown
        - field_dropdown
        - wellnames_dropdown (list of dict): contains wellnames for dropdown
        - user_selection

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    #----------------------------------------
    # Clear dropdowns if button clicked
    #----------------------------------------
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if geom_clear and 'geometry-clear' in trigger_id: geometry = []
    if form_clear and 'formation-clear' in trigger_id: formation = []
    if field_clear and 'field-clear' in trigger_id: field = []
    if wells_clear and 'wells-clear' in trigger_id: selected_wells = []

    #----------------------------------------
    # Get dataset from DB
    #----------------------------------------
    dataset = db.filter_wellnames(well_type="'Gasífero'", start_date=start_date,
        end_date=end_date)
    
    # Sort values by lateral length and fracs and drop duplicates
    dataset.sort_values(['Pozo_Form', 'Rama', 'Fracturas'], inplace=True,
        na_position='first')
    dataset.drop_duplicates(subset='Pozo_Form', keep='last', inplace=True)

    # Filter na wellnames
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

        # Assert formation
        if 'ALL' in formation and len(formation) > 1:
            if 'ALL' in previous['formation']:
                # ALL must be removed
                formation.remove('ALL')
            else:
                # Only keep ALL
                for f in formation: formation.remove(f)
                formation.append('ALL')
            
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
    # Filter by formation
    #----------------------------------------
    if (not formation
        or 'ALL' in formation):
        # None or ALL selected, do not filter
        mask_form = dataset['Pozo_Form'].notna()
    else:
        # Keep only selected formations
        mask_form = ~dataset['Pozo_Form'].notna()
        for form in formation:
            mask_form = np.logical_or(mask_form, dataset['Formacion'] == form)
    
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
    if (latlen_start is None) and (latlen_end is None):
        # None selected, do not filter
        mask_latlen = dataset['Pozo_Form'].notna()
    
    elif (latlen_start is None) and (latlen_end is not None):
        # Keep only below latlen_end value
        mask_latlen = dataset['Rama'] <= latlen_end
        
        # Take NaNs lateral length as zero
        mask_latlen = np.logical_or(mask_latlen, dataset['Rama'].isna())

    elif (latlen_start is not None) and (latlen_end is None):
        # Keep only above latlen_start value
        mask_latlen = dataset['Rama'] >= latlen_start

    else:
        # Keep only between selected values
        mask_latlen = np.logical_and(dataset['Rama'] >= latlen_start,
            dataset['Rama'] <= latlen_end)

    #----------------------------------------
    # Filter by fracs
    #----------------------------------------
    if (fracs_start is None) and (fracs_end is None):
        # None selected, do not filter
        mask_fracs = dataset['Pozo_Form'].notna()
    
    elif (fracs_start is None) and (fracs_end is not None):
        # Keep only below fracs_end value
        mask_fracs = dataset['Fracturas'] <= fracs_end

        # Take NaNs fracs as zero
        mask_fracs = np.logical_or(mask_fracs, dataset['Fracturas'].isna())

    elif (fracs_start is not None) and (fracs_end is None):
        # Keep only above fracs_start value
        mask_fracs = dataset['Fracturas'] >= fracs_start

    else:
        # Keep only between selected values
        mask_fracs = np.logical_and(dataset['Fracturas'] >= fracs_start,
            dataset['Fracturas'] <= fracs_end)

    #----------------------------------------
    # Update geometry dropdown
    #----------------------------------------
    geometry_dropdown = []
    
    # Wells without lateral length (Vertical)
    if np.logical_or(
        dataset[mask_well & mask_form & mask_field & mask_latlen & mask_fracs]
            ['Rama'].isna(),
        dataset[mask_well & mask_form & mask_field & mask_latlen & mask_fracs]
            ['Rama'] == 0
        ).any():
        if 'ALL' in geometry:
            geometry_dropdown.append({
                'label': 'Vertical',
                'value': 'V',
                'disabled': True
            })
        else:
            geometry_dropdown.append({'label': 'Vertical', 'value': 'V'})

    # Wells with lateral length (Horizontal)
    if (dataset[mask_well & mask_form & mask_field & mask_latlen & mask_fracs]
        ['Rama'] > 0
        ).any():
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
    # Update formation dropdown
    #----------------------------------------
    if 'ALL' in formation:
        formation_dropdown = [{'label': form, 'value': form, 'disabled': True}
            for form in np.sort(dataset[mask_well & mask_geom & mask_field
            & mask_latlen & mask_fracs]['Formacion'].unique())]
    else:
        formation_dropdown = [{'label': form, 'value': form} for form in
            np.sort(dataset[mask_well & mask_geom & mask_field & mask_latlen
            & mask_fracs]['Formacion'].unique())]
    
    # Append 'select all' option
    if formation_dropdown:
        formation_dropdown.insert(0, {'label': 'Seleccionar todos', 'value': 'ALL'})

    #----------------------------------------
    # Update field dropdown
    #----------------------------------------
    field_dropdown = []

    if 'ALL' in field:
        field_dropdown = [{'label': f, 'value': f, 'disabled': True}
            for f in np.sort((
            dataset[mask_well & mask_geom & mask_form & mask_latlen & mask_fracs]
            ['Empresa']
            + ' > ' + dataset[mask_well & mask_geom & mask_form & mask_latlen
            & mask_fracs]['Yacimiento']).unique())]
    else:
        field_dropdown = [{'label': f, 'value': f}
            for f in np.sort((
            dataset[mask_well & mask_geom & mask_form & mask_latlen & mask_fracs]
            ['Empresa']
            + ' > ' + dataset[mask_well & mask_geom & mask_form & mask_latlen
            & mask_fracs]['Yacimiento']).unique())]
    
    # Append 'select all' option
    if field_dropdown:
        field_dropdown.insert(0, {'label': 'Seleccionar todos', 'value': 'ALL'})

    #----------------------------------------
    # Update wellnames dropdown
    #----------------------------------------
    mask = mask_well & mask_geom & mask_form & mask_field & mask_latlen & mask_fracs
    dataset_filtered = dataset[mask]

    wellnames_dropdown = [{'label': w, 'value': w} for w in
        dataset_filtered['Pozo_Form'].tolist()]

    # Append 'select all' option
    select_all_warning_className = 'hide-element'
    if wellnames_dropdown and len(wellnames_dropdown) <= 250:
        wellnames_dropdown.insert(0, {'label': 'Seleccionar todos', 'value': 'ALL'})
    elif 'ALL' in selected_wells:
        selected_wells.remove('ALL')
        if wellnames_dropdown:
            select_all_warning_className = 'select-all-warning'
    elif wellnames_dropdown:
        select_all_warning_className = 'select-all-warning'

    #----------------------------------------
    # Update user selection data and values
    #----------------------------------------
    user_selection = json.dumps({
        'geometry': geometry,
        'formation': formation,
        'field': field
    })

    # Update geometry values
    for geom in geometry:
        if geom not in [each['value'] for each in geometry_dropdown]:
            geometry.remove(geom)

    # Update formation values
    for form in formation:
        if form not in [each['value'] for each in formation_dropdown]:
            formation.remove(form)

    # Update field values
    for f in field:
        if f not in [each['value'] for each in field_dropdown]:
            field.remove(f)

    # Update lateral length min and max
    latlen_min = dataset[mask_well & mask_geom & mask_form
        & mask_field & mask_fracs]['Rama'].min()
    latlen_max = dataset[mask_well & mask_geom & mask_form
        & mask_field & mask_fracs]['Rama'].max()

    # Update fracs min and max
    fracs_min = dataset[mask_well & mask_geom & mask_form
        & mask_field & mask_latlen]['Fracturas'].min()
    fracs_max = dataset[mask_well & mask_geom & mask_form
        & mask_field & mask_latlen]['Fracturas'].max()

    return (geometry_dropdown, geometry, formation_dropdown, formation,
        field_dropdown, field, wellnames_dropdown, selected_wells, user_selection,
        latlen_min, latlen_max, latlen_min, latlen_max, latlen_min, latlen_max,
        fracs_min, fracs_max, fracs_min, fracs_max, fracs_min, fracs_max,
        select_all_warning_className)
    

@app.callback(
    Output('gas-filtered-data', 'data'),

    Input('gas-wells-dropdown', 'value'),

    State('gas-wells-dropdown', 'options')    
)
def filter_dataset(selected_wells, wellnames_dropdown):
    '''
    Filters dataset based on wells selected.

    Params:
        - selected_wells (list of str): contains selected wells from dropdown
        - wellnames_dropdown (list of dict): contains wellnames for dropdown

    Returns:
        - gas_filtered_data (str): json containing wells data from DB

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    if 'ALL' in selected_wells:
        selected_wells = [option.get('value') for option in wellnames_dropdown]
        selected_wells.remove('ALL')
    
    dataset = db.filter_dataset(selected_wells)
    
    return dataset.to_json(date_format='iso', orient='split')


@app.callback(
    Output('gas-wells-info-table', 'data'),

    Input('gas-filtered-data', 'data'),
)
def update_wells_info_table(filtered_data_json):
    '''
    Updates wells info table based on wells selected.

    Params:
        filtered_data_json ():

    Returns:
        info_table_rows ():

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''
    
    # JSON to pandas dataFrame
    dataset = pd.read_json(filtered_data_json, orient='split')

    # Order by wellname, TdP, qg_ef, qo_ef
    dataset.sort_values(['Pozo_Form', 'TdP', 'qg_ef', 'qo_ef'], inplace=True)
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
            'qg_avg': [dff['qg_avg'].iloc[-1]],
            'proppant': [dff['ArenaTotal'].iloc[-1]],
            'water_inj': [dff['agua_inyectada_m3'].iloc[-1] * 6.2898107438466 / 1000]
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
        row['proppant'] = '{:,.0f}'.format(row['proppant'])
        row['water_inj'] = '{:,.0f}'.format(row['water_inj'])

    return info_table_rows
    
    
@app.callback([
    Output('gas-qg-vs-tdp', 'figure'),
    Output('gas-qg-vs-gp', 'figure'),
    Output('gas-gp-vs-tdp', 'figure'),
    Output('gas-gor-vs-gp', 'figure'),
    Output('gas-gor-vs-tdp', 'figure'),
    Output('gas-qo-vs-tdp', 'figure'),
    Output('gas-np-vs-tdp', 'figure'),
    Output('gas-history-forecasts-table', 'data'),
    Output('gas-EUR-forecasts-table', 'data'),
    Output('gas-forecasts', 'data')],

    [Input('gas-filtered-data', 'data'),
    Input('gas-wells-dropdown', 'value'),
    Input('gas-btn-decline-auto', 'className'),
    Input('gas-fix-last-q', 'value'),
    Input('gas-fc-log-scale', 'value'),
    Input('gas-dca-auto-model', 'value'),
    Input('gas-dca-auto-exp-start-input', 'value'),
    Input('gas-dca-auto-forecast-end-time-input', 'value'),
    Input('gas-dca-auto-forecast-q-lim-input', 'value'),
    Input('gas-dca-auto-GOR-method', 'value'),
    Input('gas-dca-auto-GORi', 'value'),
    Input('gas-dca-auto-Gp-pb', 'value'),
    Input('gas-dca-auto-GORmax', 'value'),
    Input('gas-dca-auto-Gp-GORmax', 'value'),
    Input('gas-dca-auto-GORf', 'value'),
    Input('gas-dca-auto-Gp-GORf', 'value'),
    Input('gas-dca-auto-GOR-a', 'value'),
    Input('gas-frac-stages-norm', 'value'),
    Input('gas-frac-stages-norm-input', 'value'),
    Input('gas-frac-latlen-norm', 'value'),
    Input('gas-frac-latlen-norm-input', 'value')],

    State('gas-wells-dropdown', 'options')
)
def update_graphs_n_tables(filtered_data_json, selected_wells, dca_auto_class,
    dca_auto_fix_last_q, log_scale, dca_auto_model, dca_auto_exp_start_input,
    dca_auto_forecast_end_time, dca_auto_q_lim, dca_auto_GOR_method, dca_auto_GORi,
    dca_auto_Gp_pb, dca_auto_GORmax, dca_auto_Gp_GORmax, dca_auto_GORf,
    dca_auto_Gp_GORf, dca_auto_GOR_a, frac_stages_norm, frac_stages_norm_value,
    frac_latlen_norm, frac_latlen_norm_value, wellnames_dropdown):
    '''
    Decodes the json filtered data (stored on tab session), then calculates the
    forecasts and updates rates and cumulatives graphs and tables based on user
    selection.

    Params:
        - filtered_data_json (str): json containing wells data from DB
        - selected_wells (list of str): contains selecter wells from dropdown
        - dca_type (str | None): decline model with one of the following:
            - 'DCA_OFF': no decline curve
            - 'DCA_AUTO': decline curve with regression parameters
            - 'DCA_MANUAL': decline curve with manual parameters
            - None if user clears dropdown
        - graph_config (list of str): contains graphs config with several of the
            following:
            - 'FIX_LAST_Q': applies offset to rate curve to fit last historical
            rate 
        - log_scale (bool): contains rate graphs scale
        - dca_model (str | None): contains model for decline, one of the following:
            - 'HYP': hyperbolic
            - 'HM': modified hyperbolic
            - None: uses previous dca_model
        - exp_start_method (str): contains method for hyperbolic-exponential 
            switching on HM model, one of the following:
            - 'EXP_START_TIME': switch based on number of days
            - 'EXP_START_DT': switch based on decline rate [%/yr]
        - exp_start_input (float | None): specifies the exp_start_method switching
            value. None value does not calculate forecasts
        - forecast_end_time (float | None): years for forecasting. None value does
            not calculate forecasts
        - q_lim (float | None): limit for economic rate
        - qi (float | None): used only when dca_type == 'DCA_MANUAL'. Oil
            rate at peak for forecasting. None value does not calculate forecasts
        - ti (float | None): used only when dca_type == 'DCA_MANUAL'. Time
            at oil rate peak for forecasting. None value does not calculate
            forecasts
        - b (float | None): used only when dca_type == 'DCA_MANUAL'. B
            parameter for hyperbolic section of the forecast. None value does
            not calculate forecasts
        - d (float | None): used only when dca_type == 'DCA_MANUAL'. Di
            parameter for hyperbolic section of the forecast. None value does
            not calculate forecasts

    Returns:
        - fig_qg (plotly.go.figure): represents the figure for oil rates forecasts
        - fig_cumg (plotly.go.figure): represents the figure for oil cumulative 
            forecasts
        - rows (list of dict): rows for the DataTable with historical + forecast
            data

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    #----------------------------------------
    # Initial setup
    #----------------------------------------
    dca_type = []
    if 'pressed' in dca_auto_class: dca_type.append('DCA_AUTO')

    if 'ALL' in selected_wells:
        selected_wells = [option.get('value') for option in wellnames_dropdown]
        selected_wells.remove('ALL')

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
        height = 450,
        margin = dict(l=20, r=20, b=20, t=35),
        yaxis = axis_config,
        xaxis = axis_config,
        showlegend = False
    )

    #----------------------------------------
    # Extract wells data
    #----------------------------------------
    dataset_filtered = pd.read_json(filtered_data_json, orient='split')
    wells_data, _, wells = dca.extract_wells_data(dataset_filtered, selected_wells)

    # Store selected wells data
    for well_data in wells_data:
        wellname = well_data['Pozo_Form'].iloc[0]
        wells[wellname] = {
            'wellname': wellname,
            'well_data': well_data,
            'normalization': {'enabled': False}
        }

    #----------------------------------------
    # Normalize if necessary
    #----------------------------------------
    if frac_stages_norm:
        for wellname in wells.keys():
            well = dca.normalize_by_fracs(wells[wellname], 'fracstages',
                frac_stages_norm_value)

    if frac_latlen_norm:
        for wellname in wells.keys():
            well = dca.normalize_by_fracs(wells[wellname], 'latlen',
                frac_latlen_norm_value)

    #----------------------------------------
    # Gas rates
    #----------------------------------------
    fig_qg_vs_Gp = go.Figure(layout=plot_layout)
    fig_qg_vs_t = go.Figure(layout=plot_layout)

    # Add historical rate to figure for selected wells
    for i, wellname in enumerate(wells.keys()):
        dca.add_fig_trace(i, fig_qg_vs_Gp, wells[wellname], 'qg_v_Gp', 'history')
        dca.add_fig_trace(i, fig_qg_vs_t, wells[wellname], 'qg', 'history')

    # If DCA_AUTO is checked, calculate forecast
    if 'DCA_AUTO' in dca_type:
        for i, wellname in enumerate(wells.keys()):
            # Calculate rates forecast
            wells[wellname] = dca.gas_dca(wells[wellname], dca_auto_model,
                dca_auto_exp_start_input, dca_auto_forecast_end_time)

            if dca_auto_fix_last_q:
                # Apply offset to meet last q
                wells[wellname] = dca.apply_dca_offset(wells[wellname], 'gas')
            
            # Trim curve
            wells[wellname] = dca.trim_curve(wells[wellname],
                dca_auto_forecast_end_time, dca_auto_q_lim, 'gas')

            # Add forecast trace to figure
            dca.add_fig_trace(i, fig_qg_vs_Gp, wells[wellname], 'qg_v_Gp', 'forecast')
            dca.add_fig_trace(i, fig_qg_vs_t, wells[wellname], 'qg', 'forecast')
    
    # Else if DCA_MANUAL is checked, calculate forecast
    elif 'DCA_MANUAL' in dca_type:
        pass

    # Plot setup
    fig_qg_vs_Gp.update_layout(
        title_text = 'Caudal de gas',
        xaxis_title = 'Gp [Mm³]',
        yaxis_title = 'qg [Mm3/d]'
    )

    # Plot setup
    fig_qg_vs_t.update_layout(
        title_text = 'Caudal de gas',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'qg [Mm3/d]'
    )

    #----------------------------------------
    # Gas cumulatives
    #----------------------------------------
    fig_cumg = go.Figure(layout=plot_layout)

    # Add historical cumulative to figure for selected wells
    for i, wellname in enumerate(wells.keys()):
        dca.add_fig_trace(i, fig_cumg, wells[wellname], 'cumg', 'history')

    # If DCA auto is checked, add forecast trace to figure
    if 'DCA_AUTO' in dca_type:
        for i, wellname in enumerate(wells.keys()):
            # This loop is used to match traces color for wells
            dca.add_fig_trace(i, fig_cumg, wells[wellname], 'cumg', 'forecast')

    # Plot setup
    fig_cumg.update_layout(
        title_text = 'Acumulada de gas',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'Gp [Mm3]'
    )

    #----------------------------------------
    # GOR
    #----------------------------------------
    fig_GOR_v_Gp = go.Figure(layout=plot_layout)
    fig_GOR_v_tdp = go.Figure(layout=plot_layout)

    # Add historical GOR to figure for selected wells
    for i, wellname in enumerate(wells.keys()):
        # Add historical trace to figures
        dca.add_fig_trace(i, fig_GOR_v_Gp, wells[wellname], 'GOR_v_Gp', 'history')
        dca.add_fig_trace(i, fig_GOR_v_tdp, wells[wellname], 'GOR_v_tdp', 'history')

    # GOR forecast
    if 'DCA_AUTO' in dca_type:
        for i, wellname in enumerate(wells.keys()):
            if 'GOR_AUTO' in dca_auto_GOR_method:
                wells[wellname] = dca.GOR_forecast(wells[wellname], 'gas')
            else:
                wells[wellname] = dca.GOR_manual_forecast(wells[wellname],
                    dca_auto_GORi, dca_auto_Gp_pb, dca_auto_GORmax,
                    dca_auto_Gp_GORmax, dca_auto_GORf, dca_auto_Gp_GORf,
                    dca_auto_GOR_a/1000)

            # Add forecast trace to figures
            dca.add_fig_trace(i, fig_GOR_v_Gp, wells[wellname], 'GOR_v_Gp', 'forecast')
            dca.add_fig_trace(i, fig_GOR_v_tdp, wells[wellname], 'GOR_v_tdp', 'forecast')
    
    # Plot setup
    fig_GOR_v_Gp.update_layout(
        title_text = 'GOR',
        xaxis_title = 'Gp [Mm3]',
        yaxis_title = 'GOR [m3/m3]'
    )

    fig_GOR_v_tdp.update_layout(
        title_text = 'GOR',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'GOR [m3/m3]'
    )

    #----------------------------------------
    # Oil rates
    #----------------------------------------
    fig_qo = go.Figure(layout=plot_layout)

    # Add historical oil to figure for selected wells
    for i, wellname in enumerate(wells.keys()):
        dca.add_fig_trace(i, fig_qo, wells[wellname], 'qo', 'history')

    # If DCA auto is checked, calculate forecast
    if 'DCA_AUTO' in dca_type:
        for i, wellname in enumerate(wells.keys()):
            wells[wellname] = dca.oil_forecast(wells[wellname])

            # Add forecast trace to figure
            dca.add_fig_trace(i, fig_qo, wells[wellname], 'qo', 'forecast', params=False)

    # Plot setup
    fig_qo.update_layout(
        title_text = 'Caudal de petróleo',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'qo [m3/d]'
    )

    #----------------------------------------
    # Oil cumulatives
    #----------------------------------------
    fig_Np = go.Figure(layout=plot_layout)

    # Add historical oil to figure for selected wells
    for i, wellname in enumerate(wells.keys()):
        dca.add_fig_trace(i, fig_Np, wells[wellname], 'cumo', 'history')

    # If DCA auto is checked, calculate forecast
    if 'DCA_AUTO' in dca_type:
        for i, wellname in enumerate(wells.keys()):
            # Calculate cumulatives forecast
            wells[wellname] = dca.cumulative(wells[wellname], 'oil')

            # Add forecast trace to figure
            dca.add_fig_trace(i, fig_Np, wells[wellname], 'cumo', 'forecast')

    # Else if DCA_MANUAL is checked, calculate forecast
    elif 'DCA_MANUAL' in dca_type:
        pass

    # Plot setup
    fig_Np.update_layout(
        title_text = 'Acumulada de petróleo',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'Np [m3]'
    )

    #----------------------------------------
    # Plots config
    #----------------------------------------
    if log_scale:
        fig_qo.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
        fig_qg_vs_Gp.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
        fig_qg_vs_t.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
    
    #----------------------------------------
    # Generate rates table
    #----------------------------------------
    dca_table = pd.DataFrame({})

    if 'DCA_AUTO' in dca_type:
        for well in wells:
            # Count number of well records
            records_num = len(wells[well]['well_data']['TdP']) + len(
                wells[well]['t_forecast'])
            GOR_pos = len(wells[well]['well_data']['TdP'])

            # Append well data to Pronos_DCA dataframe
            aux_dict = {
                'Pozo_Form_P': np.repeat(well, records_num),
                'TdP': np.append(wells[well]['well_data']['TdP'].values,
                    wells[well]['t_forecast']),
                'qo': np.append(wells[well]['well_data']['qo_ef'].values,
                    wells[well]['qo_forecast']),
                'Np': np.append(wells[well]['well_data']['Acu_Pet'].values,
                    wells[well]['cumo_forecast']),
                'GOR': np.append(wells[well]['well_data']['GOR_ef'].values,
                    wells[well]['GOR_forecast'][GOR_pos:]),
                'qg': np.append(wells[well]['well_data']['qg_ef'].values,
                    wells[well]['qg_forecast']),
                'Gp': np.append(wells[well]['well_data']['Acu_Gas'].values,
                    wells[well]['cumg_forecast']),
            }

            aux_df = pd.DataFrame.from_dict(aux_dict)
            dca_table = pd.concat([dca_table, aux_df])
    else:
        for well in wells:
            # Count number of well records
            records_num = len(wells[well]['well_data']['TdP'])

            # Append well data to dca_table dataframe
            aux_dict = {
                'Pozo_Form_P': np.repeat(well, records_num),
                'TdP': wells[well]['well_data']['TdP'].values,
                'qo': wells[well]['well_data']['qo_ef'].values,
                'Np': wells[well]['well_data']['Acu_Pet'].values,
                'GOR': wells[well]['well_data']['GOR_ef'].values,
                'qg': wells[well]['well_data']['qg_ef'].values,
                'Gp': wells[well]['well_data']['Acu_Gas'].values,
            }

            aux_df = pd.DataFrame.from_dict(aux_dict)
            dca_table = pd.concat([dca_table, aux_df])
        
    if 'DCA_MANUAL' in dca_type:
        pass

    # Set rows
    rows = dca_table.to_dict('records')

    # Format rows
    for row in rows:
        row['TdP'] = '{:,.0f}'.format(row['TdP'])
        row['qo'] = '{:,.2f}'.format(row['qo'])
        row['Np'] = '{:,.0f}'.format(row['Np'])
        row['GOR'] = '{:,.0f}'.format(row['GOR'])
        row['qg'] = '{:,.3f}'.format(row['qg'])
        row['Gp'] = '{:,.0f}'.format(row['Gp'])

    #----------------------------------------
    # Generate EUR table
    #----------------------------------------
    eur_table = pd.DataFrame({})

    if 'DCA_AUTO' in dca_type:
        for well in wells:
            
            EUR_oil = wells[well]['well_data']['Acu_Pet'].iloc[-1]
            EUR_gas = wells[well]['well_data']['Acu_Gas'].iloc[-1]

            if wells[well]['t_forecast'].size:
                mask = ~np.isnan(wells[well]['cumo_forecast'])
                if wells[well]['cumo_forecast'][mask].size:
                    EUR_oil = wells[well]['cumo_forecast'][mask][-1]
                            
                mask = ~np.isnan(wells[well]['cumg_forecast'])
                if wells[well]['cumg_forecast'][mask].size:
                    EUR_gas = wells[well]['cumg_forecast'][mask][-1]

            if wells[well]['well_data']['Rama'].iloc[-1]:
                EUR_oil_ll = (EUR_oil * 6.2898107438466 / 
                    wells[well]['well_data']['Rama'].iloc[-1] / 1000)
            else:
                EUR_oil_ll = np.nan
            
            # Get normalized frac stages values to show on table
            if (wells[well]['normalization']['enabled']
                and wells[well]['normalization'].get('fracstages', '')):
                frac_stages = wells[well]['normalization'].get('fracstages')
            else:
                frac_stages = wells[well]['well_data']['Fracturas'].iloc[-1]

            # Get normalized latlen values to show on table
            if (wells[well]['normalization']['enabled']
                and wells[well]['normalization'].get('latlen', '')):
                lat_len = wells[well]['normalization'].get('latlen')
            else:
                lat_len = wells[well]['well_data']['Rama'].iloc[-1]

            aux_dict = {
                'Pozo_Form_P': well,
                'b': [wells[well]['b']],
                'd_hyp': [wells[well]['d_hyp']],
                'd_exp': [wells[well]['d_exp']],
                'Fracturas': [wells[well]['well_data']['Fracturas'].iloc[-1]],
                'Frac_norm': [frac_stages],
                'Rama': [wells[well]['well_data']['Rama'].iloc[-1]],
                'Rama_norm': [lat_len],
                'EUR_oil': [EUR_oil],
                'EUR_oil_bbl': [EUR_oil * 6.2898107438466 / 1000],
                'EUR_oil_fracs': [EUR_oil * 6.2898107438466 / 1000 / frac_stages],
                'EUR_oil_ll': [EUR_oil_ll],
                'EUR_gas': [EUR_gas],
                'EUR_gas_scf': [EUR_gas * 1000 * 35.31467 / 1E6],
                'EUR_gas_fracs': [EUR_gas * 1000 * 35.31467 / 1E6 / frac_stages]
            }

            aux_df = pd.DataFrame.from_dict(aux_dict)
            eur_table = pd.concat([eur_table, aux_df])
    
    # Set rows
    rows_eur = eur_table.to_dict('records')

    # Format rows
    for row in rows_eur:
        row['Fracturas'] = '{:,.0f}'.format(row['Fracturas'])
        row['Frac_norm'] = '{:,.0f}'.format(row['Frac_norm'])
        row['Rama'] = '{:,.0f}'.format(row['Rama'])
        row['Rama_norm'] = '{:,.0f}'.format(row['Rama_norm'])
        row['EUR_oil'] = '{:,.2f}'.format(row['EUR_oil'])
        row['EUR_oil_bbl'] = '{:,.2f}'.format(row['EUR_oil_bbl'])
        row['EUR_oil_fracs'] = '{:,.2f}'.format(row['EUR_oil_fracs'])
        row['EUR_oil_ll'] = '{:,.2f}'.format(row['EUR_oil_ll'])
        row['EUR_gas'] = '{:,.2f}'.format(row['EUR_gas'])
        row['EUR_gas_scf'] = '{:,.2f}'.format(row['EUR_gas_scf'])
        row['EUR_gas_fracs'] = '{:,.2f}'.format(row['EUR_gas_fracs'])

    #----------------------------------------
    # Process forecasts to store in session
    #----------------------------------------
    if 'DCA_MANUAL' in dca_type: pass
    gas_forecasts_json = dca.serialize_forecast(wells)

    return (fig_qg_vs_t, fig_qg_vs_Gp, fig_cumg, fig_GOR_v_Gp, fig_GOR_v_tdp,
        fig_qo, fig_Np, rows, rows_eur, gas_forecasts_json)


@app.callback(
    [Output('gas-db-checklist', 'options'),
    Output('gas-read-db-toast', 'data')],

    [Input('gas-db-sidebar-update-btn', 'n_clicks'),
    Input('gas-btn-forecasts-from-db', 'n_clicks')],

    State('session', 'data')
)
def update_db_sidebar_checklist(update_btn, ribbon_click, session):
    '''
    TODO: AGREGAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    if ribbon_click and ribbon_click % 2:
        toast_header = 'Consultar DB'
        checklist = []

        # If button is clicked, query DB
        try:
            if session and 'LOGGED_IN' in session: session_dict = json.loads(session)

            result = db.read_my_forecasts('parameters', None, session_dict)

            # Build checklist
            for forecast_ID in result['ID_Pronos']:
                params = dca.get_params_from_forecast_ID(forecast_ID)
                checklist.append({'label': params[6], 'value': forecast_ID})

            toast_msg = 'Pronósticos cargados desde DB correctamente.'
            toast_icon = "success"
            toast_duration = 4000 # Milisecs

        except Exception as err:
            toast_msg = f'Ocurrió un error al cargar los pronósticos de DB. [{err}]'
            toast_duration = None
            toast_icon = "warning"
        
        toast = {
            'db-msg': {
                'children': toast_msg
            },
            'db-toast': {
                'is_open': True,
                'header': toast_header,
                'duration': toast_duration,
                'icon': toast_icon
            }
        }
        
        return checklist, json.dumps(toast)
    
    return no_update, no_update
    
 
@app.callback(
    [Output('gas-qo-vs-tdp_db', 'figure'),
    Output('gas-np-vs-tdp_db', 'figure'),
    Output('gas-gor-vs-gp_db', 'figure'),
    Output('gas-gor-vs-tdp_db', 'figure'),
    Output('gas-qg-vs-tdp_db', 'figure'),
    Output('gas-qg-vs-gp_db', 'figure'),
    Output('gas-gp-vs-tdp_db', 'figure'),
    Output('gas-my_forecasts', 'data')],

    [Input('gas-db-checklist', 'value'),
    Input('gas-fc-log-scale', 'value')],

    [State('session', 'data'),
    State('gas-my_forecasts', 'data')]
)
def update_plots_from_db(forecasts_ids, log_scale, session, my_forecasts_json):
    '''
    TODO: AGREGAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    #----------------------------------------
    # Initial setup
    #----------------------------------------
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
        height = 450,
        margin = dict(l=20, r=20, b=20, t=35),
        yaxis = axis_config,
        xaxis = axis_config,
        showlegend = False
    )

    # Read current state of my forecasts
    if (my_forecasts_json is not None) and len(json.loads(my_forecasts_json)):
        my_forecasts = {'df': pd.DataFrame(json.loads(my_forecasts_json))}
        my_forecasts['ids'] = my_forecasts['df']['ID_Pronos'].unique()
    else:
        my_forecasts = {'ids': []}
        my_forecasts['df'] = pd.DataFrame({})

    # Get selected forecasts from DB
    selected_forecasts_ids = []
    if session and 'LOGGED_IN' in session and forecasts_ids:
        session_dict = json.loads(session)
        forecasts_ids = pd.Series(forecasts_ids)

        # Selected forecasts wellnames
        wellnames = [dca.get_params_from_forecast_ID(x)[6] for x in forecasts_ids]
        normalize = [re.search(r'_norm_(.*:.*)_', x).group()[:-1]
            if 'norm' in x else '' for x in forecasts_ids]
        
        # Append history ids
        history_ids = 'H_' + pd.Series(wellnames) + pd.Series(normalize)
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
    
        selected_forecasts_ids = list(ids.unique())

    #----------------------------------------
    # Add traces to plot
    #----------------------------------------
    wells = {}

    fig_qo = go.Figure(layout=plot_layout)
    fig_cumo = go.Figure(layout=plot_layout)
    fig_GOR_v_Gp = go.Figure(layout=plot_layout)
    fig_GOR_v_tdp = go.Figure(layout=plot_layout)
    fig_qg = go.Figure(layout=plot_layout)
    fig_qg_vs_Gp = go.Figure(layout=plot_layout)
    fig_cumg = go.Figure(layout=plot_layout)

    for i, forecast_id in enumerate(selected_forecasts_ids):
        # Get well name
        wellname = forecast_id

        wells[wellname] = {
            'wellname': wellname,
            'well_data': my_forecasts['df'].loc[ \
                my_forecasts['df']['ID_Pronos'] == forecast_id].sort_values(by=['TdP'])
        }

        dca.add_fig_trace(i, fig_qo, wells[wellname], 'qo', 'history')
        dca.add_fig_trace(i, fig_cumo, wells[wellname], 'cumo', 'history')

        dca.add_fig_trace(i, fig_GOR_v_Gp, wells[wellname], 'GOR_v_Gp', 'history')
        dca.add_fig_trace(i, fig_GOR_v_tdp, wells[wellname], 'GOR_v_tdp', 'history')

        dca.add_fig_trace(i, fig_qg, wells[wellname], 'qg', 'history')
        dca.add_fig_trace(i, fig_qg_vs_Gp, wells[wellname], 'qg_v_Gp', 'history')
        dca.add_fig_trace(i, fig_cumg, wells[wellname], 'cumg', 'history')

    #----------------------------------------
    # Plots config
    #----------------------------------------
    fig_qo.update_layout(
        title_text = 'Caudal de petróleo (Pronósticos en DB)',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'qo [m3/d]'
    )

    fig_cumo.update_layout(
        title_text = 'Acumulada de petróleo (Pronósticos en DB)',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'Np [m3]'
    )

    fig_GOR_v_Gp.update_layout(
        title_text = 'GOR (Pronósticos en DB)',
        xaxis_title = 'Gp [m3]',
        yaxis_title = 'GOR [m3/m3]'
    )

    fig_GOR_v_tdp.update_layout(
        title_text = 'GOR (Pronósticos en DB)',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'GOR [m3/m3]'
    )

    fig_qg.update_layout(
        title_text = 'Caudal de gas (Pronósticos en DB)',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'qg [Mm3/d]'
    )

    # Plot setup
    fig_qg_vs_Gp.update_layout(
        title_text = 'Caudal de gas (Pronósticos en DB)',
        xaxis_title = 'Gp [Mm³]',
        yaxis_title = 'qg [Mm3/d]'
    )

    fig_cumg.update_layout(
        title_text = 'Acumulada de gas (Pronósticos en DB)',
        xaxis_title = 'TdP [d]',
        yaxis_title = 'Gp [Mm3]'
    )

    if log_scale:
        fig_qo.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
        fig_qg.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)
        fig_qg_vs_Gp.update_yaxes(type = 'log', tickformat = ',.0f', tickfont_size = 10)

    return (fig_qo, fig_cumo, fig_GOR_v_Gp, fig_GOR_v_tdp, fig_qg, fig_qg_vs_Gp,
        fig_cumg, my_forecasts['df'].to_json())
        
 
@app.callback(
    [Output('gas-dca-auto-controls', 'is_open'),
    Output('gas-dca-auto-exp-start-method', 'disabled'),
    Output('gas-dca-auto-exp-start-input', 'disabled'),
    Output('gas-dca-auto-exp-start-input', 'placeholder'),
    Output('gas-dca-auto-exp-start-input', 'max'),
    Output('gas-dca-auto-exp-start-input', 'min'),
    Output('gas-dca-auto-GORi', 'disabled'),
    Output('gas-dca-auto-Gp-pb', 'disabled'),
    Output('gas-dca-auto-GORmax', 'disabled'),
    Output('gas-dca-auto-Gp-GORmax', 'disabled'),
    Output('gas-dca-auto-GORf', 'disabled'),
    Output('gas-dca-auto-Gp-GORf', 'disabled'),
    Output('gas-dca-auto-GOR-a', 'disabled'),
    Output('gas-frac-stages-norm-input', 'disabled'),
    Output('gas-frac-latlen-norm-input', 'disabled'),],

    [Input('gas-btn-decline-auto', 'className'),
    Input('gas-dca-auto-model', 'value'),
    Input('gas-dca-auto-exp-start-method', 'value'),
    Input('gas-dca-auto-GOR-method', 'value'),
    Input('gas-frac-stages-norm', 'value'),
    Input('gas-frac-latlen-norm', 'value')])
def show_hide_model_controls(dca_auto_class, dca_auto_model,
    dca_auto_exp_start_method, dca_auto_GOR_method, frac_stages_norm,
    frac_latlen_norm):
    '''
    Changes visibility and style of decline model controls based on user
    configuration.

    Params:
        - dca_type (str | None): decline model with one of the following:
            - 'DCA_OFF': no decline curve
            - 'DCA_AUTO': decline curve with regression parameters
            - 'DCA_MANUAL': decline curve with manual parameters
            - None if user clears dropdown. Behaves like 'DCA_OFF'
        - dca_model (str | None): contains model for decline, one of the following:
            - 'HYP': hyperbolic
            - 'HM': modified hyperbolic
            - None: uses previous dca_model visibility
        - exp_start_method (str): contains method for hyperbolic-exponential 
            switching on HM model, one of the following:
            - 'EXP_START_TIME': switch based on number of days
            - 'EXP_START_DT': switch based on decline rate [%/yr]

    Returns:
        - select_dca_model_disabled (bool): disables dca_model dropdown. Takes
            True when dca_type == 'DCA_OFF'
        - select_dca_model_style (dict): 
        - exp_start_method_disabled (bool):
        - exp_start_method_style (dict):
        - exp_start_input_disabled (bool)
        - exp_start_input_style (dict):
        - exp_start_input_placeholder (str):
        - exp_start_input_max (float):
        - exp_start_input_min (float):
        - forecast_end_time_input_disabled (bool):
        - forecast_end_time_input_style (dict):
        - manual_dca_config_open (bool):
        - auto_dca_config_open (bool):

    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    dca_type = []
    if 'pressed' in dca_auto_class: dca_type.append('DCA_AUTO')

    # Auto DCA controls visibility
    dca_auto_controls_open = ('DCA_AUTO' in dca_type)
    dca_auto_exp_start_method_disabled = ('HM' not in dca_auto_model)
    dca_auto_exp_start_input_disabled = ('HM' not in dca_auto_model)
    dca_auto_exp_start_input_min = 1

    if 'EXP_START_TIME' in dca_auto_exp_start_method:
        dca_auto_exp_start_input_placeholder = 'días'
        dca_auto_exp_start_input_max = 18262
    else:
        dca_auto_exp_start_input_placeholder = 'D anual'
        dca_auto_exp_start_input_max = 500
    
    dca_auto_GOR_input_disable = ('GOR_AUTO' in dca_auto_GOR_method)

    # Normalization input visibility
    frac_stages_norm_input_disabled = not frac_stages_norm
    frac_latlen_norm_input_disabled = not frac_latlen_norm

    return (dca_auto_controls_open,
        dca_auto_exp_start_method_disabled,
        dca_auto_exp_start_input_disabled,
        dca_auto_exp_start_input_placeholder,
        dca_auto_exp_start_input_max,
        dca_auto_exp_start_input_min,
        dca_auto_GOR_input_disable,
        dca_auto_GOR_input_disable,
        dca_auto_GOR_input_disable,
        dca_auto_GOR_input_disable,
        dca_auto_GOR_input_disable,
        dca_auto_GOR_input_disable,
        dca_auto_GOR_input_disable,
        frac_stages_norm_input_disabled,
        frac_latlen_norm_input_disabled)
        
        
@app.callback(
    [Output('gas-wells-info-container', 'is_open'),
    Output('gas-dca-EUR-container', 'is_open'),
    Output('gas-wells-info-button', 'n_clicks'),
    Output('gas-wells-info-button', 'className')],

    Input('gas-wells-info-button', 'n_clicks'),

    [State('gas-wells-info-container', 'is_open'),
    State('gas-wells-info-button', 'className')]
)
def show_hide_wells_info(button_click, container_open, className):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    if button_click:
        if 'pressed' in className:
            return ~container_open, ~container_open, 0, 'ribbon-btn'
        else:
            return ~container_open, ~container_open, 0, 'ribbon-btn-pressed'

    return False, False, 0, className


@app.callback(
    [Output('gas-qg-tdp-db-forecast-container', 'is_open'),
    Output('gas-qg-gp-db-forecast-container', 'is_open'),
    Output('gas-gp-tdp-db-forecast-container', 'is_open'),
    Output('gas-GOR-gp-db-forecast-container', 'is_open'),
    Output('gas-GOR-tdp-db-forecast-container', 'is_open'),
    Output('gas-qo-tdp-db-forecast-container', 'is_open'),
    Output('gas-np-tdp-db-forecast-container', 'is_open')],

    Input('gas-btn-forecasts-from-db', 'className')
)
def show_hide_db_forecast_plots(btn_className):
    '''
    TODO: COMPLETAR DOCSTRING
    
    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    is_open = 'pressed' in btn_className
    
    return is_open, is_open, is_open, is_open, is_open, is_open, is_open


@app.callback(
    Output('gas-db-toast', 'data'),

    Input('gas-forecasts-to-db', 'n_clicks'),

    [State('gas-forecasts', 'data'),
    State('session', 'data')]
)
def export_gas_forecast_db(export_button_click, gas_forecasts, session):
    '''
    Exports gas forecasts to DB and shows toast with results

    Params:
        - export_button_click (int):
        - gas_forecasts (str): json
        - session (str): json

    Returns:
        - toast (dict):
    
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    toast_header = 'Exportar a DB'
    
    # If button is clicked, export to DB
    if export_button_click:
        try:
            if session and 'LOGGED_IN' in session: session_dict = json.loads(session)

            db.forecasts_to_sql(gas_forecasts, session_dict, 'gas')
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
    [Output("gas-filter-sidebar-expanded", "className"),
    Output("gas-filter-sidebar-collapsed", "className"),
    Output("gas-db-sidebar-expanded", "className"),
    Output("gas-db-sidebar-collapsed", "className"),
    Output("gas-container", "className")],

    [Input("gas-filter-sidebar-collapse-btn", "n_clicks"),
    Input("gas-filter-sidebar-expand-btn", "n_clicks"),
    Input('gas-btn-forecasts-from-db', 'n_clicks'),
    Input("gas-db-sidebar-collapse-btn", "n_clicks"),
    Input("gas-db-sidebar-expand-btn", "n_clicks")],

    [State("gas-filter-sidebar-expanded", "className"),
    State("gas-db-sidebar-expanded", "className")]
)
def toggle_collapse_sidebars(*args):
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
    
    # Initialize outputs
    filter_sidebar_expanded_class = no_update
    filter_sidebar_collapsed_class = no_update
    db_sidebar_expanded_class = no_update
    db_sidebar_collapsed_class = no_update
    main_container_class = no_update

    # Check if forecasts from db is enabled
    fc_from_db_enabled = 0
    if args[2]: fc_from_db_enabled = args[2] % 2
    
    # Check if db sidebar is expanded or collapsed
    if fc_from_db_enabled:
        if 'hide' in args[6]:
            # Db sidebar is collapsed
            db_sidebar_expanded = False
        else:
            # Db sidebar is expanded
            db_sidebar_expanded = True

    if 'filter-sidebar-collapse' in trigger_id:
        filter_sidebar_expanded_class = 'hide-element'
        filter_sidebar_collapsed_class = 'show-filter-sidebar-collapsed'

        if fc_from_db_enabled:
            if db_sidebar_expanded:
                main_container_class = 'left-collapsed-right-expanded'
            else:
                main_container_class = 'left-collapsed-right-collapsed'
        else:
            main_container_class = 'left-collapsed'
            
    if 'gas-filter-sidebar-expand-btn' in trigger_id:
        filter_sidebar_expanded_class = 'show-filter-sidebar-expanded'
        filter_sidebar_collapsed_class = 'hide-element'

        if fc_from_db_enabled:
            if db_sidebar_expanded:
                main_container_class = 'left-expanded-right-expanded'
            else:
                main_container_class = 'left-expanded-right-collapsed'
        else:
            main_container_class = 'left-expanded' 

    # Check if filter sidebar is expanded or collapsed
    if 'hide' in args[5]:
        # Filter sidebar is collapsed
        filter_sidebar_expanded = False
    else:
        # Filter sidebar is expanded
        filter_sidebar_expanded = True
    
    if ('gas-btn-forecasts-from-db' in trigger_id or
        'gas-db-sidebar-expand-btn' in trigger_id):
        if fc_from_db_enabled:
            db_sidebar_expanded_class = 'show-db-sidebar-expanded'
            db_sidebar_collapsed_class = 'hide-element'

            if filter_sidebar_expanded:
                main_container_class = 'left-expanded-right-expanded'
            else:
                main_container_class = 'left-collapsed-right-expanded' 
        else:
            db_sidebar_expanded_class = 'hide-element'
            db_sidebar_collapsed_class = 'hide-element'

            if filter_sidebar_expanded:
                main_container_class = 'left-expanded'
            else:
                main_container_class = 'left-collapsed'

    if 'gas-db-sidebar-collapse-btn' in trigger_id:
        db_sidebar_expanded_class = 'hide-element'
        db_sidebar_collapsed_class = 'show-db-sidebar-collapsed'

        if filter_sidebar_expanded:
            main_container_class = 'left-expanded-right-collapsed' 
        else:
            main_container_class = 'left-collapsed-right-collapsed' 

    return (filter_sidebar_expanded_class,
        filter_sidebar_collapsed_class,
        db_sidebar_expanded_class,
        db_sidebar_collapsed_class,
        main_container_class)


@app.callback(
    [Output('gas-fix-last-q', 'className'),
    Output('gas-frac-stages-norm', 'className'),
    Output('gas-frac-latlen-norm', 'className')],

    [Input('gas-fix-last-q', 'value'),
    Input('gas-frac-stages-norm', 'value'),
    Input('gas-frac-latlen-norm', 'value')]
)
def toggle_on_off(fix_last_q_on, frac_stages_norm_on, frac_latlen_norm_on):
    '''
    TODO: COMPLETAR DOCSTRING

    Ariel Cabello (acabello@fdc-group.com) - May 2022
    '''

    if fix_last_q_on:
        fix_last_q_btn = 'toggle-switch-colored'
    else:
        fix_last_q_btn = 'toggle-switch'

    if frac_stages_norm_on:
        frac_stages_norm_btn = 'toggle-switch-colored'
    else:
        frac_stages_norm_btn = 'toggle-switch'

    if frac_latlen_norm_on:
        frac_latlen_norm_btn = 'toggle-switch-colored'
    else:
        frac_latlen_norm_btn = 'toggle-switch'
    
    return fix_last_q_btn, frac_stages_norm_btn, frac_latlen_norm_btn


app.clientside_callback(
    """
    function(n_clicks, n_clicks2) {
        if (n_clicks > 0 || n_clicks2)
            document.querySelector("#gas-history-forecasts-table button.export").click()
        return ""
    }
    """,
    Output('gas-export-table-xls', 'data-dummy'),

    [Input('gas-export-table-xls', 'n_clicks'),
    Input('gas-export-forecast', 'n_clicks')]
)

app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0)
            document.querySelector("#gas-wells-info-table button.export").click()
        return ""
    }
    """,
    Output('gas-export-wells-info', 'data-dummy'),
    Input('gas-export-wells-info', 'n_clicks')
)

app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0)
            document.querySelector("#gas-history-forecasts-table button.export").click()
        return ""
    }
    """,
    Output('gas-export-wells-eur', 'data-dummy'),
    Input('gas-export-wells-eur', 'n_clicks')
)