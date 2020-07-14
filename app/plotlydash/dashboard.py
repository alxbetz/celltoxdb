import dash

import dash_html_components as html
import dash_core_components as dcc
import dash_daq as daq
import pandas as pd
import numpy as np
from .layout import html_layout

from app import db
from query_lib import get_database_readable


def log_button(ename,scale='Log'):
    """
    Button for switching between linear and log scale on axes

    Parameters
    ----------
    ename : string
        html id name.
    scale : string, optional
        Default value for axis. The default is 'Log'.

    Returns
    -------
    RatioItem
       dash object for radiobuttons

    """
    return dcc.RadioItems(id=ename,
                          options=[{
                              'label': i,
                              'value': i
                          } for i in ['Linear', 'Log']],
                          value=scale,
                          labelStyle={'display': 'inline-block'})


def dropdown(ename, indicators, default):
    """ render dropdown field """
    return dcc.Dropdown(id=ename,
                        options=[{
                            'label': i,
                            'value': i
                        } for i in indicators],
                        value=default)


def range_slider(ename, df, colname, step):
    """ render a range slider """
    return html.Div(
        dcc.RangeSlider(
            id=ename,
            min=df[colname].min(),
            max=df[colname].max(),
            value=[df[colname].min(), df[colname].max()],
            #marks={"{:.{}f}".format(x, 1 ): "{:.{}f}".format(x, 1 ) for x in np.arange(np.floor(df[colname].min() * 10) / 10,np.ceil(df[colname].max() * 10) / 10,0.3)},
            marks={
                "{:.{}f}".format(x, 0): "{:.{}f}".format(x, 0)
                for x in np.arange(-10, 100)
            },
            step=step),
        style={
            'width': '100%',
            'padding': '5px 0px 20px 0px'
        })


def create_dashboard(server):
    """Create the Dash app."""

    external_stylesheets = [
        '/static/css/dash.css', {
            'href': '/static/css/dash.css',
            'rel': 'stylesheet',
            'integrity':
            'sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO',
            'crossorigin': 'anonymous'
        }
    ]

    dash_app = dash.Dash(server=server, routes_pathname_prefix='/dashapp/')

    # Load data from database
    q = get_database_readable(db)

    if q.count() == 0:
        return dash_app.server
    df = pd.DataFrame(q)
    # Custom HTML layout
    dash_app.index_string = html_layout
    #with open(os.path.join("app","templates","plot.html"),"r") as f:
    #    dash_app.index_string = f.read()

    available_indicators = df['cell_line'].unique()
    endpoint_indicators = df['endpoint'].unique()
    endpoint_indicators_all = np.append("all", df['endpoint'].unique())
    chemical_indicators = np.append("all", df.chemical_name.unique())
    chemical_property_indicators = [
        'logKow', 'solubility', 'henry\'s law constant'
    ]
    come_indicators = ["nominal & measured", "nominal", "measured"]
    timepoint_indicators = np.append("all", np.sort(df.timepoint.unique()))

    dash_app.layout = \
     html.Div(id="site-wrapper",children=[
         html.Div(id="left-board",children=[
             html.H4(children="Global Filters"),
             html.Div(html.P("Chemical")),
             html.Div(dropdown('crossfilter-chemical',chemical_indicators,'all')),
             html.Div(html.P("Cell-line")),
             html.Div(dropdown('crossfilter-cell_line',np.append("all",available_indicators),'all')),
             html.Div(html.P("Endpoint")),
             html.Div(dropdown('crossfilter-endpoint',endpoint_indicators_all,'all')),
             html.Div(html.P("Timepoint [h]")),
             html.Div(dropdown('crossfilter-timepoint',timepoint_indicators,'all')),
             html.Div(html.P("logKow")),
             html.Div(range_slider('crossfilter-kow--rangeslider',df,"experimental_log_kow",0.1)),
             html.Div(html.P("x-concentration")),
             html.Div(dropdown('crossfilter-x-come',come_indicators,'nominal & measured')),
             html.Div(html.P("y-concentration")),
             html.Div(dropdown('crossfilter-y-come',come_indicators,'nominal & measured')),
             html.Br(),
             html.Div(daq.BooleanSwitch(
                  id = "crossfilter-uml",
                  on=False,
                  label="show in umol/L",
                  labelPosition="top"
                )

             ),
             html.Br()
         ]),
         html.Div(id="right-board",children=[
             html.Div(id="top-left-box",children=[html.H4(children="Cell line comparison"),
                     html.Div([
            dropdown('crossfilter-xaxis-column',available_indicators,'RTgill-W1'),
            log_button('crossfilter-xaxis-type')
            ],style={"width" : "49%","float" : "left"}),
        html.Div([
            dropdown('crossfilter-yaxis-column',available_indicators,'RTgutGC'),
            log_button('crossfilter-yaxis-type')
            ],style={"width" : "49%","float" : "right"}),

        html.Div(children=[dcc.Graph(id='crossfilter-indicator-scatter')],
                 style={'width': '100%', 'display': 'inline-block', 'padding': '0 20'})

             ]),
             html.Div(id="top-right-box",children=[html.H4(children="Endpoint Comparison"),
                 html.Div([
                dropdown('crossfilter-xaxis-column-chemical',endpoint_indicators,'alamarBlue'),
                log_button('crossfilter-xaxis-type-chemical')
                ],style={"width" : "49%","float" : "left"}),
                html.Div([
                dropdown('crossfilter-yaxis-column-chemical',endpoint_indicators,'Neutral Red'),
                log_button('crossfilter-yaxis-type-chemical')
                ],style={"width" : "49%","float" : "right"}),
        html.Div(children=[dcc.Graph(id='crossfilter-indicator-scatter-chemical')],
                 style={'width': '100%', 'display': 'inline-block', 'padding': '0 20'})


            ]),
             html.Div(id="bottom-left-box",children=[
                 html.H4(children="Chemical properties"),
                 html.Div([
                dropdown('filter-chemical-property',chemical_property_indicators,'logKow'),
                log_button('xaxis-type-chemical-property'),
                log_button('yaxis-type-chemical-property')
                ],style={"width" : "49%","float" : "left"}),
                 html.Div(children=[dcc.Graph(id='ec50-logkow')],
                 style={'width': '100%', 'display': 'inline-block', 'padding': '0 20'})])
         ])
          ])

    init_callbacks(dash_app, df)

    return dash_app.server


def get_priority(x):

    if x == "user_corrected_experimental":
        return 0
    elif x == "experimental":
        return 1
    else:
        return 2


def get_chemprop(df, name):
    uce = "user_corrected_experimental_" + name
    e = "experimental_" + name
    p = "estimated_" + name
    dff = df[["cas_number", uce, e, p]].drop_duplicates()
    dff = dff.melt(id_vars=["cas_number"]).dropna()
    dff = dff.assign(
        variable = lambda dataframe : dataframe['variable']. \
            map(lambda variable: variable.replace("_"+name,""))
               ,
        priority = lambda dataframe: dataframe['variable'].map(get_priority))
    dff = dff.sort_values("priority").groupby("cas_number").first()
    return dff.drop("priority", axis=1).rename(columns={
        "variable": name + "_determination",
        "value": name
    })


def init_callbacks(dash_app, df):
    @dash_app.callback(
        dash.dependencies.Output('crossfilter-indicator-scatter', 'figure'), [
            dash.dependencies.Input('crossfilter-xaxis-column', 'value'),
            dash.dependencies.Input('crossfilter-yaxis-column', 'value'),
            dash.dependencies.Input('crossfilter-xaxis-type', 'value'),
            dash.dependencies.Input('crossfilter-yaxis-type', 'value'),
            dash.dependencies.Input('crossfilter-kow--rangeslider', 'value'),
            dash.dependencies.Input('crossfilter-endpoint', 'value'),
            dash.dependencies.Input('crossfilter-chemical', 'value'),
            dash.dependencies.Input('crossfilter-timepoint', 'value'),
            dash.dependencies.Input('crossfilter-x-come', 'value'),
            dash.dependencies.Input('crossfilter-y-come', 'value'),
            dash.dependencies.Input('crossfilter-uml', 'on')
        ])
    def update_graph(xaxis_column_name, yaxis_column_name, xaxis_type,
                     yaxis_type, log_kow, endpoint, chemical, timepoint, xcome,
                     ycome, uml):
        #dff = df[df['experimental_log_kow'] == experimental_log_kow]
        lox = (df['user_corrected_experimental_log_kow'] >= log_kow[0])  \
            | (df['experimental_log_kow'] >= log_kow[0])  \
            | (df['estimated_log_kow'] >= log_kow[0])
        hix = (df['user_corrected_experimental_log_kow'] <= log_kow[1])  \
            | (df['experimental_log_kow'] <= log_kow[1])  \
            | (df['estimated_log_kow'] <= log_kow[1])
        dff = df[lox & hix]
        if chemical != "all":
            dff = dff[dff["chemical_name"] == chemical]
        if endpoint != "all":
            dff = dff[dff["endpoint"] == endpoint]
        if timepoint != "all":
            timepoint = int(timepoint)
            dff = dff[[x == timepoint for x in dff["timepoint"]]]

        print("---- uml")
        print(uml)

        if uml:
            dff["ec50"] = (dff["ec50"] / dff["molecular_weight"]) * 1000
            unit = "[umol/L]"
        else:
            unit = "[mg/L]"

        xdat = dff[dff['cell_line'] == xaxis_column_name]
        ydat = dff[dff['cell_line'] == yaxis_column_name]

        xfil = xdat[[
            'chemical_name', "cas_number", "endpoint", "experimental_log_kow",
            "conc_determination", "ec50"
        ]]
        yfil = ydat[[
            'chemical_name', "cas_number", "endpoint", "conc_determination",
            "ec50"
        ]]
        #xfil.cas_number = xfil.cas_number.astype(str)
        #yfil.loc[:,('cas_number')]= yfil.loc[:,('cas_number')].astype(str)
        pdf = xfil.merge(yfil, on=['cas_number', 'endpoint'])
        print(df.columns)

        if ycome != "nominal & measured":
            fvaly = 'me' if ycome == "measured" else "no"
            pdf = pdf[pdf['conc_determination_y'] == fvaly]
        if xcome != "nominal & measured":
            fvalx = 'me' if xcome == "measured" else "no"
            pdf = pdf[pdf['conc_determination_x'] == fvalx]
        print(pdf)
        return {
            'data': [
                dict(x=pdf['ec50_x'],
                     y=pdf['ec50_y'],
                     text=pdf['chemical_name_x'],
                     customdata=pdf['chemical_name_x'],
                     mode='markers',
                     marker={
                         'size': 15,
                         'opacity': 0.5,
                         'line': {
                             'width': 0.5,
                             'color': 'white'
                         }
                     })
            ],
            'layout':
            dict(xaxis={
                'title': xaxis_column_name + " EC50 " + unit,
                'type': 'linear' if xaxis_type == 'Linear' else 'log'
            },
                 yaxis={
                     'title': yaxis_column_name + " EC50 " + unit,
                     'type': 'linear' if yaxis_type == 'Linear' else 'log'
                 },
                 margin={
                     'l': 40,
                     'b': 30,
                     't': 10,
                     'r': 0
                 },
                 height=450,
                 hovermode='closest',
                 annotations=[
                     dict(text="n = %s" % pdf.shape[0],
                          x=1 if xaxis_type == 'Linear' else min(
                              np.log10(pdf['ec50_x'])),
                          y=max(pdf['ec50_y']) if yaxis_type == 'Linear' else
                          max(np.log10(pdf['ec50_y'])),
                          showarrow=False)
                 ])
        }

    @dash_app.callback(
        dash.dependencies.Output('crossfilter-indicator-scatter-chemical',
                                 'figure'),
        [
            dash.dependencies.Input('crossfilter-xaxis-column-chemical',
                                    'value'),
            dash.dependencies.Input('crossfilter-yaxis-column-chemical',
                                    'value'),
            dash.dependencies.Input('crossfilter-xaxis-type-chemical',
                                    'value'),
            dash.dependencies.Input('crossfilter-yaxis-type-chemical',
                                    'value'),
            dash.dependencies.Input('crossfilter-kow--rangeslider', 'value'),
            dash.dependencies.Input('crossfilter-chemical', 'value'),
            dash.dependencies.Input('crossfilter-cell_line', 'value'),
            dash.dependencies.Input('crossfilter-timepoint', 'value'),
            dash.dependencies.Input('crossfilter-x-come', 'value'),
            dash.dependencies.Input('crossfilter-y-come', 'value'),
            dash.dependencies.Input('crossfilter-uml', 'on')
        ])
    def update_graph_chemical(xaxis_column_name, yaxis_column_name, xaxis_type,
                              yaxis_type, log_kow, chemical, cell_line,
                              timepoint, xcome, ycome, uml):
        #dff = df[df['experimental_log_kow'] == experimental_log_kow]
        lox = (df['user_corrected_experimental_log_kow'] >= log_kow[0])  \
            | (df['experimental_log_kow'] >= log_kow[0])  \
            | (df['estimated_log_kow'] >= log_kow[0])
        hix = (df['user_corrected_experimental_log_kow'] <= log_kow[1])  \
            | (df['experimental_log_kow'] <= log_kow[1])  \
            | (df['estimated_log_kow'] <= log_kow[1])
        dff = df[lox & hix]
        if chemical != "all":
            dff = dff[dff["chemical_name"] == chemical]
        if cell_line != "all":
            dff = dff[dff["cell_line"] == cell_line]
        if timepoint != "all":
            timepoint = int(timepoint)
            dff = dff[[x == timepoint for x in dff["timepoint"]]]

        if uml:
            dff["ec50"] = (dff["ec50"] / dff["molecular_weight"]) * 1000
            unit = "[umol/L]"
        else:
            unit = "[mg/L]"

        xdat = dff[dff['endpoint'] == xaxis_column_name]
        ydat = dff[dff['endpoint'] == yaxis_column_name]

        xfil = xdat[[
            'chemical_name', "cas_number", "endpoint", "experimental_log_kow",
            "conc_determination", "ec50"
        ]]
        yfil = ydat[[
            'chemical_name', "cas_number", "endpoint", "conc_determination",
            "ec50"
        ]]
        #xfil.cas_number = xfil.cas_number.astype(str)
        #yfil.loc[:,('cas_number')]= yfil.loc[:,('cas_number')].astype(str)
        pdf = xfil.merge(yfil, on=['cas_number'])

        if ycome != "nominal & measured":
            fvaly = 'me' if ycome == "measured" else "no"
            pdf = pdf[pdf['conc_determination_y'] == fvaly]
        if xcome != "nominal & measured":
            fvalx = 'me' if xcome == "measured" else "no"
            pdf = pdf[pdf['conc_determination_x'] == fvalx]

        #print("ENDPOINTS")
        #print(pdf)

        return {
            'data': [
                dict(x=pdf['ec50_x'],
                     y=pdf['ec50_y'],
                     text=pdf['chemical_name_x'],
                     customdata=pdf['chemical_name_x'],
                     mode='markers',
                     marker={
                         'size': 15,
                         'opacity': 0.5,
                         'line': {
                             'width': 0.5,
                             'color': 'white'
                         }
                     })
            ],
            'layout':
            dict(
                xaxis={
                    'title': xaxis_column_name + " EC50 " + unit,
                    'type': 'linear' if xaxis_type == 'Linear' else 'log'
                },
                yaxis={
                    'title': yaxis_column_name + " EC50 " + unit,
                    'type': 'linear' if yaxis_type == 'Linear' else 'log'
                },
                margin={
                    'l': 40,
                    'b': 30,
                    't': 10,
                    'r': 0
                },
                height=450,
                hovermode='closest',
                annotations=[
                    dict(text="n = %s" % pdf.shape[0],
                         x=np.nanmin(pdf['ec50_x']) if xaxis_type == 'Linear'
                         else np.nanmin(np.log10(pdf['ec50_x'])),
                         y=np.nanmax(pdf['ec50_y'][pdf['ec50_y'] != np.inf])
                         if yaxis_type == 'Linear' else np.nanmax(
                             np.log10(pdf['ec50_y'][pdf['ec50_y'] != np.inf])),
                         showarrow=False)
                ])
        }

    @dash_app.callback(dash.dependencies.Output('ec50-logkow', 'figure'), [
        dash.dependencies.Input('xaxis-type-chemical-property', 'value'),
        dash.dependencies.Input('yaxis-type-chemical-property', 'value'),
        dash.dependencies.Input('crossfilter-kow--rangeslider', 'value'),
        dash.dependencies.Input('crossfilter-chemical', 'value'),
        dash.dependencies.Input('filter-chemical-property', 'value'),
        dash.dependencies.Input('crossfilter-cell_line', 'value'),
        dash.dependencies.Input('crossfilter-timepoint', 'value'),
        dash.dependencies.Input('crossfilter-uml', 'on')
    ])
    def update_graph_kow(xaxis_type, yaxis_type, log_kow, chemical,
                         chemical_property, cell_line, timepoint, uml):
        lox = (df['user_corrected_experimental_log_kow'] >= log_kow[0])  \
            | (df['experimental_log_kow'] >= log_kow[0])  \
            | (df['estimated_log_kow'] >= log_kow[0])
        hix = (df['user_corrected_experimental_log_kow'] <= log_kow[1])  \
            | (df['experimental_log_kow'] <= log_kow[1])  \
            | (df['estimated_log_kow'] <= log_kow[1])
        dff = df[lox & hix]
        if uml:
            dff["ec50"] = (dff["ec50"] / dff["molecular_weight"]) * 1000
            unit = "[umol/L]"
        else:
            unit = "[mg/L]"

        if chemical != "all":
            dff = dff[dff["chemical_name"] == chemical]
        if cell_line != "all":
            dff = dff[dff["cell_line"] == cell_line]
        if timepoint != "all":
            dff = dff[dff["timepoint"] == timepoint]

        chemical_property_map = {
            'logKow': "log_kow",
            "solubility": "solubility",
            "henry\'s law constant": "henry_constant"
        }

        df_kow = get_chemprop(dff, chemical_property_map[chemical_property])
        dff = dff.merge(df_kow, on="cas_number", how="left")
        print(dff)
        print("test")
        return {
            'data': [
                dict(x=dff[chemical_property_map[chemical_property]],
                     y=dff['ec50'],
                     text=dff['chemical_name'],
                     customdata=dff['chemical_name'],
                     mode='markers',
                     marker={
                         'size': 15,
                         'opacity': 0.5,
                         'line': {
                             'width': 0.5,
                             'color': 'white'
                         }
                     })
            ],
            'layout':
            dict(xaxis={
                'title': chemical_property,
                'type': 'linear' if xaxis_type == 'Linear' else 'log'
            },
                 yaxis={
                     'title': "EC50 " + unit,
                     'type': 'linear' if yaxis_type == 'Linear' else 'log'
                 },
                 margin={
                     'l': 40,
                     'b': 30,
                     't': 10,
                     'r': 0
                 },
                 height=450,
                 hovermode='closest')
        }
