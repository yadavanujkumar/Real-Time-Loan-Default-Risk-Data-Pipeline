# Usage Examples

## Quick Start Examples

### Example 1: Running the Full Pipeline

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30

# Run the full pipeline
python main.py --mode full
```

This will:
1. Ingest data from APIs (or generate mock data)
2. Process features
3. Train ML model
4. Load data to warehouse
5. Generate risk report

### Example 2: Real-time Streaming

```python
# Start streaming for 5 minutes
python main.py --mode stream --duration 300
```

### Example 3: Dashboard Monitoring

```bash
# Start the dashboard
python main.py --mode dashboard

# Access at http://localhost:8050
```

## API Integration Examples

### Using RazorpayX API

```python
from src.ingestion.api_client import FintechAPIClient
from datetime import datetime, timedelta

client = FintechAPIClient()

# Fetch last 7 days of transactions
start_date = datetime.now() - timedelta(days=7)
end_date = datetime.now()

transactions = client.get_razorpay_transactions(
    start_date=start_date,
    end_date=end_date,
    limit=100
)

print(f"Fetched {len(transactions)} transactions")
```

### Using Plaid API

```python
from src.ingestion.api_client import FintechAPIClient

client = FintechAPIClient()

# Get account balance
balance = client.get_plaid_balance(
    access_token='your_plaid_access_token'
)

# Get transactions
transactions = client.get_plaid_transactions(
    access_token='your_plaid_access_token',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

## Kafka Streaming Examples

### Producing Data to Kafka

```python
from src.ingestion.kafka_producer import LoanDataProducer

producer = LoanDataProducer()

# Send a loan application
loan_data = {
    'application_id': 'app_12345',
    'customer_id': 'cust_67890',
    'loan_amount': 50000.0,
    'annual_income': 80000.0,
    'credit_score': 720,
    'debt_amount': 15000.0
}

success = producer.send_loan_application(loan_data)
print(f"Sent: {success}")

producer.close()
```

### Consuming Data from Kafka

```python
from src.ingestion.kafka_consumer import LoanDataConsumer

def process_message(topic, message):
    """Process each message"""
    print(f"Topic: {topic}")
    print(f"Data: {message}")
    # Add your processing logic here

consumer = LoanDataConsumer()
consumer.consume_messages(
    process_function=process_message,
    max_messages=10
)
```

## Feature Engineering Examples

### Computing Risk Features

```python
import pandas as pd
from src.processing.feature_engineering import RiskFeatureEngineer

# Sample loan data
loan_data = pd.DataFrame({
    'customer_id': ['cust_1', 'cust_2'],
    'loan_amount': [25000, 35000],
    'annual_income': [60000, 90000],
    'debt_amount': [10000, 15000],
    'employment_length': [5, 8],
    'credit_limit': [20000, 40000]
})

# Engineer features
engineer = RiskFeatureEngineer()
enriched_data = engineer.create_all_features(loan_data)

print(enriched_data[['customer_id', 'debt_to_income_ratio', 
                     'credit_utilization', 'default_probability']])
```

### Custom Feature Calculation

```python
from src.processing.feature_engineering import RiskFeatureEngineer

engineer = RiskFeatureEngineer()

# Calculate individual features
df = engineer.calculate_debt_to_income_ratio(loan_data)
df = engineer.calculate_credit_utilization(df)
df = engineer.calculate_income_stability_score(df)

# Create risk categories
df = engineer.create_risk_categories(df)
```

## ML Model Examples

### Training a Model

```python
import pandas as pd
from src.models.loan_default_model import LoanDefaultModel

# Load training data
training_data = pd.read_csv('training_data.csv')

# Initialize model
model = LoanDefaultModel(model_type='random_forest')

# Prepare features
X, y = model.prepare_features(training_data, target_col='default')

# Train
metrics = model.train(X, y, test_size=0.2, scale_features=True)

print(f"Model Metrics: {metrics}")

# Save model
model.save_model('models/loan_model.pkl')
```

### Making Predictions

```python
from src.models.loan_default_model import LoanDefaultModel
import pandas as pd

# Load trained model
model = LoanDefaultModel()
model.load_model('models/loan_model.pkl')

# New applications
new_applications = pd.DataFrame({
    'debt_to_income_ratio': [0.3, 0.6],
    'credit_utilization': [0.4, 0.8],
    'loan_to_value_ratio': [0.5, 1.2],
    'income_stability_score': [0.8, 0.5]
})

# Predict
predictions = model.predict(new_applications)
probabilities = model.predict_proba(new_applications)

print(f"Predictions: {predictions}")
print(f"Default Probabilities: {probabilities}")
```

### Feature Importance

```python
# Get feature importance
importance = model.get_feature_importance()
print(importance.head(10))
```

## Storage Examples

### Writing to S3

```python
import pandas as pd
from src.storage.connectors import S3Connector

s3 = S3Connector()

# Upload DataFrame
df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
s3.upload_dataframe(
    df,
    key='processed/my_data.parquet',
    file_format='parquet'
)

# Download DataFrame
downloaded_df = s3.download_dataframe(
    key='processed/my_data.parquet',
    file_format='parquet'
)
```

### Writing to Snowflake

```python
import pandas as pd
from src.storage.connectors import SnowflakeConnector

sf = SnowflakeConnector()
sf.connect()

# Write data
df = pd.DataFrame({
    'customer_id': ['c1', 'c2'],
    'risk_score': [0.3, 0.7]
})

sf.write_dataframe(df, 'loan_risk_scores', if_exists='append')

# Read data
results = sf.read_query("SELECT * FROM loan_risk_scores LIMIT 10")
print(results)

sf.close()
```

### Writing to BigQuery

```python
from src.storage.connectors import BigQueryConnector

bq = BigQueryConnector()

# Write DataFrame
bq.write_dataframe(df, 'loan_applications')

# Query data
query = """
SELECT 
    customer_id,
    AVG(default_probability) as avg_risk
FROM `project.dataset.loan_applications`
GROUP BY customer_id
HAVING avg_risk > 0.5
"""

high_risk_customers = bq.read_query(query)
```

## Spark Streaming Examples

### Processing Kafka Stream

```python
from src.processing.stream_processor import LoanStreamProcessor

processor = LoanStreamProcessor()

# Read stream
loan_stream = processor.read_kafka_stream(
    topic='loan-applications',
    schema=processor.get_loan_application_schema()
)

# Write to console (for debugging)
query = processor.write_to_console(loan_stream, 'loan_debug')

# Or write to storage
query = processor.write_to_parquet(
    loan_stream,
    output_path='/data/processed/loans',
    query_name='loan_processing',
    partition_by=['date']
)

query.awaitTermination()
```

### Computing Features in Streaming

```python
processor = LoanStreamProcessor()

# Read streams
loan_stream = processor.read_kafka_stream('loan-applications', ...)
transaction_stream = processor.read_kafka_stream('transactions', ...)

# Compute features
enriched_stream = processor.compute_risk_features(
    loan_stream,
    transaction_stream
)

# Write output
processor.write_to_parquet(enriched_stream, '/output/path', 'enriched')
```

## Airflow DAG Examples

### Triggering a DAG Run

```bash
# Via CLI
airflow dags trigger loan_default_risk_pipeline

# With parameters
airflow dags trigger loan_default_risk_pipeline \
  --conf '{"batch_size": 1000, "retrain_model": true}'
```

### Monitoring DAG Status

```python
from airflow.api.client.local_client import Client

client = Client(None, None)

# Get DAG runs
runs = client.get_dag_runs('loan_default_risk_pipeline')

for run in runs:
    print(f"Run ID: {run['run_id']}, State: {run['state']}")
```

## Dashboard Customization

### Custom Visualizations

```python
# In dashboards/risk_dashboard.py

import plotly.express as px

# Add new chart
@app.callback(
    Output('custom-chart', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_custom_chart(n):
    df = load_data()
    
    fig = px.scatter_3d(
        df,
        x='debt_to_income_ratio',
        y='credit_utilization',
        z='default_probability',
        color='risk_category'
    )
    
    return fig
```

## Batch Processing Examples

### Scheduled Batch Job

```python
import schedule
import time
from src.ingestion.api_client import FintechAPIClient
from src.processing.feature_engineering import RiskFeatureEngineer

def daily_batch_job():
    """Run daily batch processing"""
    print("Starting daily batch job...")
    
    # Fetch data
    client = FintechAPIClient()
    transactions = client.get_razorpay_transactions(limit=1000)
    
    # Process features
    engineer = RiskFeatureEngineer()
    # ... processing logic
    
    print("Batch job completed")

# Schedule job
schedule.every().day.at("02:00").do(daily_batch_job)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Testing Examples

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_feature_engineering.py

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run with verbose output
pytest tests/ -v
```

### Writing Custom Tests

```python
import pytest
from src.processing.feature_engineering import RiskFeatureEngineer

def test_custom_feature():
    """Test custom feature calculation"""
    engineer = RiskFeatureEngineer()
    
    # Your test logic here
    df = pd.DataFrame({'data': [1, 2, 3]})
    result = engineer.calculate_debt_to_income_ratio(df)
    
    assert 'debt_to_income_ratio' in result.columns
```

## Performance Monitoring

### Logging Custom Metrics

```python
from src.utils.logger import setup_logger

logger = setup_logger(__name__, log_dir='logs')

# Log processing metrics
logger.info(f"Processed {record_count} records in {duration:.2f}s")
logger.warning(f"High error rate: {error_rate:.2%}")
```

### Tracking Model Performance

```python
import mlflow

with mlflow.start_run():
    # Log metrics
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("precision", 0.92)
    
    # Log parameters
    mlflow.log_param("model_type", "random_forest")
    mlflow.log_param("n_estimators", 100)
    
    # Log model
    mlflow.sklearn.log_model(model, "model")
```

## Advanced Usage

### Custom Risk Scoring Logic

```python
from src.processing.feature_engineering import RiskFeatureEngineer

class CustomRiskScorer(RiskFeatureEngineer):
    """Custom risk scoring with business rules"""
    
    def calculate_custom_risk_score(self, df):
        """Apply custom business rules"""
        df['custom_risk'] = (
            0.4 * df['debt_to_income_ratio'] +
            0.3 * df['credit_utilization'] +
            0.2 * df['late_payment_ratio'] +
            0.1 * (1 - df['income_stability_score'])
        )
        
        # Apply business rules
        df.loc[df['credit_score'] < 600, 'custom_risk'] *= 1.5
        df.loc[df['employment_length'] > 10, 'custom_risk'] *= 0.8
        
        return df
```

### Multi-Model Ensemble

```python
from src.models.loan_default_model import LoanDefaultModel

# Train multiple models
models = []
for model_type in ['random_forest', 'gradient_boosting', 'logistic']:
    model = LoanDefaultModel(model_type=model_type)
    X, y = model.prepare_features(training_data, target_col='default')
    model.train(X, y)
    models.append(model)

# Ensemble predictions
predictions = []
for model in models:
    pred = model.predict_proba(X_test)
    predictions.append(pred)

# Average predictions
ensemble_pred = np.mean(predictions, axis=0)
```

---

For more examples and detailed documentation, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [API Reference](../README.md)
