import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import datetime
import plotly.graph_objects as go

# Load the data and convert 'date' column to datetime
df_path = 'faro_potugalete-20221006_spl.csv'
# df_path = 'llodio-20211105_spl.csv'
df_name = df_path.split("/")[-1]
df = pd.read_csv(df_path)
df['date'] = pd.to_datetime(df['date'])

app = dash.Dash(__name__)

band_columns = [
    '25.12', '31.62', '39.81', '50.12', '63.1', '79.43', '100.0', '125.89', '158.49',
    '199.53', '251.19', '316.23', '398.11', '501.19', '630.96', '794.33',
    '1000.0', '1258.93', '1584.89', '1995.26', '2511.89', '3162.28',
    '3981.07', '5011.87', '6309.57', '7943.28', '10000.0', '12589.25'
]

has_band_columns = all(col in df.columns for col in band_columns)

base_options = [
    {'label': 'All', 'value': 'All'},
    {'label': 'LA', 'value': 'LA'},
    {'label': 'LC', 'value': 'LC'},
    {'label': 'LZ', 'value': 'LZ'},
    {'label': 'LAmax', 'value': 'LAmax'},
    {'label': 'LAmin', 'value': 'LAmin'},
    {'label': 'LA, LAmax, LAmin', 'value': 'LA, LAmax, LAmin'}
]

if has_band_columns:
    base_options.append({'label': 'Contour Map', 'value': 'Contour Map'})

app.layout = html.Div([
    html.H1(f"Sound Pressure Levels"),
    html.H2(children=f"{df_name}", style={'fontSize': '16px', 'margin': '10px 0', 'textAlign': 'center'}),

    # left-side container for the checkboxes
    html.Div([
        html.Label("Select Metrics:", style={'marginBottom': '10px'}),
        dcc.Checklist(
            id='metric-checklist',
            options=base_options,
            value=['LA'],
            inline=False  # Set inline to False to stack the options vertically
        ),
    ], style={
        'position': 'absolute', 
        'left': '10px',
        'top': '80px',
        'width': '100%',
        'marginTop': '30px'
    }),

    # Only include the dropdown for 1/3 Octave Band if has_band_columns is True
    html.Div([
        html.Label("1/3 Octave Band:", style={'marginBottom': '10px', 'marginTop': '20px'}),
        dcc.Dropdown(
            id='band-dropdown',
            options=[{'label': band, 'value': band} for band in band_columns] if has_band_columns else [],
            value=None,
            multi=False,
            style={'width': '27%'} if has_band_columns else {'display': 'none'}
        )
    ], style={
        'position': 'absolute', 
        'left': '10px',
        'top': '350px',
        'width': '100%',
        'display': 'block' if has_band_columns else 'none'
    }),

    # Right-side container for the date slider and graph
    html.Div([
        html.Label("Select Date Range:", style={'marginTop': '0px'}),
        dcc.RangeSlider(
            id='date-slider',
            min=int(df['date'].min().timestamp()),
            max=int(df['date'].max().timestamp()),
            step=3600,  # One hour steps
            value=[
                int(df['date'].min().timestamp()),
                int(df['date'].max().timestamp())
            ],
            marks={
                int(ts.timestamp()): {
                    'label': ts.strftime('%Y-%m-%d'),
                }
                for ts in pd.date_range(df['date'].min(), df['date'].max(), freq='D')
            }
        ),
        
        dcc.Graph(id='la-graph', style={'display': 'none'}),
        dcc.Graph(id='lc-graph', style={'display': 'none'}),
        dcc.Graph(id='lz-graph', style={'display': 'none'}),
        dcc.Graph(id='lamax-graph', style={'display': 'none'}),
        dcc.Graph(id='lamin-graph', style={'display': 'none'}),
        dcc.Graph(id='las-graph', style={'display': 'none'}),
        dcc.Graph(id='contour-graph', style={'display': 'none'}),
        dcc.Graph(id='band-graph', style={'display': 'none'}),

    ], style={'marginLeft': '200px', 'marginRight': '20px'}),
])

@app.callback(
    [Output('la-graph', 'figure'), Output('la-graph', 'style'),
     Output('lc-graph', 'figure'), Output('lc-graph', 'style'),
     Output('lz-graph', 'figure'), Output('lz-graph', 'style'),
     Output('lamax-graph', 'figure'), Output('lamax-graph', 'style'),
     Output('lamin-graph', 'figure'), Output('lamin-graph', 'style'),
     Output('las-graph', 'figure'), Output('las-graph', 'style'),
     Output('contour-graph', 'figure'), Output('contour-graph', 'style'),
     Output('band-graph', 'figure'), Output('band-graph', 'style')],
    [Input('date-slider', 'value'),
     Input('metric-checklist', 'value'),
     Input('band-dropdown', 'value')]
)

def update_graph(selected_range, selected_metrics, selected_band):
    start_date = datetime.datetime.fromtimestamp(selected_range[0])
    end_date = datetime.datetime.fromtimestamp(selected_range[1])
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    la_figure = px.line(filtered_df, x='date', y='LA', title='LA Values')
    la_figure.update_traces(line=dict(width=.5))
    lc_figure = px.line(filtered_df, x='date', y='LC', title='LC Values')
    lc_figure.update_traces(line=dict(width=.5))
    lz_figure = px.line(filtered_df, x='date', y='LZ', title='LZ Values')
    lz_figure.update_traces(line=dict(width=.5))
    lamax_figure = px.line(filtered_df, x='date', y='LAmax', title='LAmax Values')
    lamax_figure.update_traces(line=dict(width=.5))
    lamin_figure = px.line(filtered_df, x='date', y='LAmin', title='LAmin Values')
    lamin_figure.update_traces(line=dict(width=.5))
    las_figure = px.line(filtered_df, x='date', y=['LA', 'LAmax', 'LAmin'], title='LA, LAmax, LAmin Values')
    las_figure.update_traces(line=dict(width=0.5))
    
    if has_band_columns:
        # Contour Map
        contour_figure = go.Figure(data=go.Contour(z=filtered_df[band_columns].values,
                                                x=filtered_df['date'].values,
                                                y=band_columns))
        contour_figure.update_layout(title='Contour Map')
    else:
        contour_figure = {} 
    
    if selected_band:
        band_figure = px.line(filtered_df, x='date', y=selected_band, title=f'Values for {selected_band} Hz Band')
        band_figure.update_traces(line=dict(width=.5))
    else:
        band_figure = {}

    # Initialize all figures to empty and styles to 'none'
    figures = {
        'LA': ({}, {'display': 'none'}),
        'LC': ({}, {'display': 'none'}),
        'LZ': ({}, {'display': 'none'}),
        'LAmax': ({}, {'display': 'none'}),
        'LAmin': ({}, {'display': 'none'}),
        'LA, LAmax, LAmin': ({}, {'display': 'none'}),
        'Contour Map': ({}, {'display': 'none'}),
    }

    # If 'All' is selected, update all figures and styles
    if 'All' in selected_metrics:
        figures['LA'] = (la_figure, {})
        figures['LC'] = (lc_figure, {})
        figures['LZ'] = (lz_figure, {})
        figures['LAmax'] = (lamax_figure, {})
        figures['LAmin'] = (lamin_figure, {})
        figures['LA, LAmax, LAmin'] = (las_figure, {})
        figures['Contour Map'] = (contour_figure, {})
    else:
        for metric in selected_metrics:
            if metric in ['LA', 'LC', 'LZ', 'LAmax', 'LAmin', 'LA, LAmax, LAmin', 'Contour Map']:
                if metric == 'LA':
                    figures['LA'] = (la_figure, {})
                elif metric == 'LC':
                    figures['LC'] = (lc_figure, {})
                elif metric == 'LZ':
                    figures['LZ'] = (lz_figure, {})
                elif metric == 'LAmax':
                    figures['LAmax'] = (lamax_figure, {})
                elif metric == 'LAmin':
                    figures['LAmin'] = (lamin_figure, {})
                elif metric == 'LA, LAmax, LAmin':
                    figures['LA, LAmax, LAmin'] = (las_figure, {})
                elif metric == 'Contour Map':
                    figures['Contour Map'] = (contour_figure, {})
            else:
                print(f"Invalid metric: {metric}")

    results = [
        figures['LA'], figures['LC'], figures['LZ'],
        figures['LAmax'], figures['LAmin'], figures['LA, LAmax, LAmin'],
        figures['Contour Map']
    ]

    band_figure_style = {} if selected_band else {'display': 'none'}
    results.extend([(band_figure, band_figure_style)])

    # Flatten the results list
    return_values = [item for sublist in results for item in sublist]

    return return_values

# Run the app
app.run_server(debug=True, port=8051)