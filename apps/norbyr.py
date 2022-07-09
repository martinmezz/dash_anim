import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from apps import common_components
import plotly.express as px
from app import app
from flask import jsonify, request
import json



#------------------------------------------------------------------------------
# Ribbon
#------------------------------------------------------------------------------
ribbon = html.Div()
#-----------------------------------------------------------------------------
# Layout
#-----------------------------------------------------------------------------
table_header = [
    html.Thead(html.Tr([html.Th("First Name"), html.Th("Last Name")]))
]

row1 = html.Tr([html.Td("Arthur"), html.Td("Dent")])
row2 = html.Tr([html.Td("Ford"), html.Td("Prefect")])
row3 = html.Tr([html.Td("Zaphod"), html.Td("Beeblebrox")])
row4 = html.Tr([html.Td("Trillian"), html.Td("Astra")])

table_body = [html.Tbody([row1, row2, row3, row4])]
layout = html.Div([
    table_header + table_body
])

