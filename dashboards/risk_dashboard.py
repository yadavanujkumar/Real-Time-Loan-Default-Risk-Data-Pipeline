"""
Real-time dashboard for loan default risk monitoring using Dash
"""
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.storage.connectors import S3Connector, SnowflakeConnector
from src.utils.config_loader import config
from src.utils.logger import setup_logger


logger = setup_logger(__name__)


# Initialize Dash app
app = dash.Dash(__name__, title='Loan Default Risk Dashboard')

# Dashboard configuration
dashboard_config = config.get('dashboard', {})
REFRESH_INTERVAL = dashboard_config.get('refresh_interval', 30) * 1000  # Convert to ms


# Layout
app.layout = html.Div([
    html.H1('Real-Time Loan Default Risk Dashboard', 
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
    
    # Auto-refresh component
    dcc.Interval(
        id='interval-component',
        interval=REFRESH_INTERVAL,
        n_intervals=0
    ),
    
    # Summary cards
    html.Div([
        html.Div([
            html.H3('Total Applications'),
            html.H2(id='total-applications', children='0')
        ], className='card', style={'flex': 1, 'margin': 10, 'padding': 20, 
                                     'backgroundColor': '#3498db', 'color': 'white',
                                     'borderRadius': 10, 'textAlign': 'center'}),
        
        html.Div([
            html.H3('High Risk'),
            html.H2(id='high-risk-count', children='0')
        ], className='card', style={'flex': 1, 'margin': 10, 'padding': 20,
                                     'backgroundColor': '#e74c3c', 'color': 'white',
                                     'borderRadius': 10, 'textAlign': 'center'}),
        
        html.Div([
            html.H3('Low Risk'),
            html.H2(id='low-risk-count', children='0')
        ], className='card', style={'flex': 1, 'margin': 10, 'padding': 20,
                                     'backgroundColor': '#2ecc71', 'color': 'white',
                                     'borderRadius': 10, 'textAlign': 'center'}),
        
        html.Div([
            html.H3('Avg Default Prob'),
            html.H2(id='avg-default-prob', children='0%')
        ], className='card', style={'flex': 1, 'margin': 10, 'padding': 20,
                                     'backgroundColor': '#f39c12', 'color': 'white',
                                     'borderRadius': 10, 'textAlign': 'center'}),
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': 20}),
    
    # Charts row 1
    html.Div([
        html.Div([
            dcc.Graph(id='risk-distribution-pie')
        ], style={'flex': 1, 'margin': 10}),
        
        html.Div([
            dcc.Graph(id='default-probability-histogram')
        ], style={'flex': 1, 'margin': 10}),
    ], style={'display': 'flex', 'marginBottom': 20}),
    
    # Charts row 2
    html.Div([
        html.Div([
            dcc.Graph(id='debt-to-income-scatter')
        ], style={'flex': 1, 'margin': 10}),
        
        html.Div([
            dcc.Graph(id='credit-utilization-box')
        ], style={'flex': 1, 'margin': 10}),
    ], style={'display': 'flex', 'marginBottom': 20}),
    
    # Time series chart
    html.Div([
        dcc.Graph(id='applications-over-time')
    ], style={'margin': 10}),
    
    # Last updated timestamp
    html.Div(id='last-updated', 
             style={'textAlign': 'center', 'color': '#7f8c8d', 'marginTop': 20})
])


def load_data():
    """Load latest data for dashboard"""
    try:
        s3_connector = S3Connector()
        
        # Try to load latest processed data
        df = s3_connector.download_dataframe(
            f"{s3_connector.processed_prefix}loan_features_{datetime.now().strftime('%Y%m%d')}.parquet"
        )
        
        logger.info(f"Loaded {len(df)} records for dashboard")
        return df
        
    except Exception as e:
        logger.warning(f"Failed to load data: {str(e)}, using sample data")
        
        # Generate sample data for demo
        n_samples = 200
        df = pd.DataFrame({
            'customer_id': [f'cust_{i}' for i in range(n_samples)],
            'loan_amount': np.random.uniform(5000, 50000, n_samples),
            'annual_income': np.random.uniform(30000, 120000, n_samples),
            'debt_to_income_ratio': np.random.uniform(0.1, 0.8, n_samples),
            'credit_utilization': np.random.uniform(0.1, 0.9, n_samples),
            'default_probability': np.random.beta(2, 5, n_samples),
            'application_timestamp': [
                datetime.now() - timedelta(days=np.random.randint(0, 30))
                for _ in range(n_samples)
            ]
        })
        
        # Add risk categories
        df['risk_category'] = df['default_probability'].apply(
            lambda x: 'Low' if x < 0.3 else ('Medium' if x < 0.6 else 'High')
        )
        
        return df


@app.callback(
    [Output('total-applications', 'children'),
     Output('high-risk-count', 'children'),
     Output('low-risk-count', 'children'),
     Output('avg-default-prob', 'children'),
     Output('risk-distribution-pie', 'figure'),
     Output('default-probability-histogram', 'figure'),
     Output('debt-to-income-scatter', 'figure'),
     Output('credit-utilization-box', 'figure'),
     Output('applications-over-time', 'figure'),
     Output('last-updated', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Update all dashboard components"""
    
    df = load_data()
    
    # Summary statistics
    total_apps = len(df)
    high_risk = len(df[df.get('risk_category', '') == 'High'])
    low_risk = len(df[df.get('risk_category', '') == 'Low'])
    avg_prob = df.get('default_probability', pd.Series([0])).mean()
    
    # Risk distribution pie chart
    risk_counts = df.get('risk_category', pd.Series()).value_counts()
    pie_fig = go.Figure(data=[go.Pie(
        labels=risk_counts.index,
        values=risk_counts.values,
        hole=0.3,
        marker_colors=['#2ecc71', '#f39c12', '#e74c3c']
    )])
    pie_fig.update_layout(title='Risk Category Distribution', height=350)
    
    # Default probability histogram
    hist_fig = px.histogram(
        df,
        x='default_probability',
        nbins=30,
        title='Default Probability Distribution',
        color_discrete_sequence=['#3498db']
    )
    hist_fig.update_layout(height=350)
    
    # Debt-to-income scatter
    scatter_fig = px.scatter(
        df,
        x='debt_to_income_ratio',
        y='default_probability',
        color='risk_category',
        title='Debt-to-Income vs Default Probability',
        color_discrete_map={'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'}
    )
    scatter_fig.update_layout(height=350)
    
    # Credit utilization box plot
    box_fig = px.box(
        df,
        x='risk_category',
        y='credit_utilization',
        title='Credit Utilization by Risk Category',
        color='risk_category',
        color_discrete_map={'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'}
    )
    box_fig.update_layout(height=350)
    
    # Applications over time
    if 'application_timestamp' in df.columns:
        df_time = df.copy()
        df_time['date'] = pd.to_datetime(df_time['application_timestamp']).dt.date
        time_series = df_time.groupby('date').size().reset_index(name='count')
        
        time_fig = px.line(
            time_series,
            x='date',
            y='count',
            title='Loan Applications Over Time',
            markers=True
        )
        time_fig.update_traces(line_color='#3498db')
    else:
        time_fig = go.Figure()
        time_fig.update_layout(title='Applications Over Time - No Data')
    
    time_fig.update_layout(height=300)
    
    # Last updated timestamp
    last_updated = f'Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    
    return (
        f'{total_apps:,}',
        f'{high_risk:,}',
        f'{low_risk:,}',
        f'{avg_prob:.1%}',
        pie_fig,
        hist_fig,
        scatter_fig,
        box_fig,
        time_fig,
        last_updated
    )


if __name__ == '__main__':
    host = dashboard_config.get('host', '0.0.0.0')
    port = dashboard_config.get('port', 8050)
    
    logger.info(f"Starting dashboard on {host}:{port}")
    app.run_server(debug=False, host=host, port=port)
