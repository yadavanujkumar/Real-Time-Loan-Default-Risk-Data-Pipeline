# Real-Time Loan Default Risk Data Pipeline

A comprehensive end-to-end data engineering pipeline for real-time loan default risk prediction and credit analysis. This system ingests live loan application and transaction data from fintech APIs, processes it using streaming and batch ETL, and delivers model-ready data for default risk prediction.

## 🎯 Project Overview

This pipeline enables financial institutions to:
- **Ingest** real-time loan applications and transaction data from fintech APIs
- **Process** data streams using Apache Spark Structured Streaming
- **Engineer** risk features like debt-to-income ratio, credit utilization, payment delays
- **Predict** loan default probabilities using machine learning models
- **Monitor** credit risk metrics through real-time dashboards
- **Store** processed data in cloud data warehouses (Snowflake/BigQuery)

## 🏗️ Architecture

```
┌─────────────────┐
│  Fintech APIs   │
│ (RazorpayX,     │
│  Plaid)         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka/Kinesis  │ ◄─── Data Ingestion Layer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Spark Streaming │ ◄─── Stream Processing
│ Feature Eng.    │
└────────┬────────┘
         │
         ├────────────────┐
         ▼                ▼
┌──────────────┐  ┌──────────────┐
│  Snowflake/  │  │  ML Models   │
│  BigQuery    │  │  (MLflow)    │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
      ┌─────────────────┐
      │  Risk Dashboard │
      │  (Dash/Plotly)  │
      └─────────────────┘
```

## 📁 Project Structure

```
Real-Time-Loan-Default-Risk-Data-Pipeline/
├── src/
│   ├── ingestion/           # Data ingestion from APIs and Kafka
│   │   ├── kafka_producer.py
│   │   ├── kafka_consumer.py
│   │   └── api_client.py
│   ├── processing/          # Stream and batch processing
│   │   ├── stream_processor.py
│   │   └── feature_engineering.py
│   ├── storage/             # Data warehouse connectors
│   │   └── connectors.py
│   ├── models/              # ML models
│   │   └── loan_default_model.py
│   ├── orchestration/       # Airflow DAGs
│   │   └── loan_risk_dag.py
│   └── utils/               # Utilities
│       ├── config_loader.py
│       └── logger.py
├── dashboards/              # Real-time dashboards
│   └── risk_dashboard.py
├── config/                  # Configuration files
│   ├── config.yaml
│   └── .env.template
├── tests/                   # Test suite
├── docker/                  # Docker configuration
├── data/                    # Data storage
│   ├── raw/
│   ├── processed/
│   └── models/
├── logs/                    # Application logs
├── docs/                    # Documentation
├── docker-compose.yml       # Docker Compose setup
├── Dockerfile               # Docker image
├── requirements.txt         # Python dependencies
├── main.py                  # Main pipeline orchestrator
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Apache Kafka (or use Docker setup)
- AWS account (for S3) OR GCP account (for BigQuery)
- Snowflake account (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yadavanujkumar/Real-Time-Loan-Default-Risk-Data-Pipeline.git
cd Real-Time-Loan-Default-Risk-Data-Pipeline
```

2. **Set up environment variables**
```bash
cp config/.env.template config/.env
# Edit config/.env with your credentials
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start services with Docker Compose**
```bash
docker-compose up -d
```

This will start:
- Kafka and Zookeeper
- PostgreSQL (for Airflow)
- Airflow webserver and scheduler
- MLflow tracking server
- Main application
- Dashboard

### Running the Pipeline

#### Option 1: Full Pipeline (Recommended for first run)
```bash
python main.py --mode full
```

#### Option 2: Individual Components

**Batch Ingestion & Processing**
```bash
python main.py --mode batch
```

**Stream Processing**
```bash
python main.py --mode stream --duration 300
```

**Model Training**
```bash
python main.py --mode train
```

**Dashboard**
```bash
python main.py --mode dashboard
```

Then access the dashboard at: http://localhost:8050

### Accessing Services

- **Airflow UI**: http://localhost:8080 (username: airflow, password: airflow)
- **MLflow UI**: http://localhost:5000
- **Dashboard**: http://localhost:8050

## 🔧 Configuration

Edit `config/config.yaml` to customize:

- **Kafka topics and settings**
- **Spark configuration**
- **Storage connections** (Snowflake, BigQuery, S3)
- **API endpoints**
- **Feature engineering parameters**
- **Dashboard refresh intervals**

## 📊 Features

### 1. Data Ingestion
- Real-time ingestion from fintech APIs (RazorpayX, Plaid)
- Kafka/Kinesis streaming
- Batch API polling

### 2. Stream Processing
- Apache Spark Structured Streaming
- Real-time feature computation
- Windowed aggregations

### 3. Feature Engineering
- **Debt-to-Income Ratio**: Total debt / Annual income
- **Loan-to-Value Ratio**: Loan amount / Collateral value
- **Credit Utilization**: Debt / Credit limit
- **Payment Delay Metrics**: Late payment history
- **Income Stability Score**: Based on employment history

### 4. ML Models
- Random Forest Classifier
- Gradient Boosting
- Logistic Regression
- Real-time predictions
- Model versioning with MLflow

### 5. Data Storage
- **S3**: Raw and processed data lake
- **Snowflake**: Analytical data warehouse
- **BigQuery**: Alternative data warehouse
- **Parquet**: Efficient columnar storage

### 6. Orchestration
- Airflow DAGs for scheduled jobs
- Automated model retraining
- Daily batch updates

### 7. Monitoring Dashboard
- Real-time risk metrics
- Default probability distributions
- Risk category breakdowns
- Time-series analysis
- Interactive visualizations with Plotly

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## 📈 Pipeline Workflow

1. **Data Ingestion**
   - APIs fetched every 6 hours via Airflow DAG
   - Transaction streams consumed from Kafka in real-time

2. **Processing**
   - Spark Structured Streaming processes events in 30-second windows
   - Features computed on-the-fly
   - Batch processing for historical data

3. **ML Pipeline**
   - Models trained on processed features
   - Predictions generated for new applications
   - Model performance tracked in MLflow

4. **Storage**
   - Raw data stored in S3
   - Processed features in Snowflake/BigQuery
   - Models versioned in MLflow registry

5. **Visualization**
   - Dashboard auto-refreshes every 30 seconds
   - Real-time risk scores displayed
   - Alerts for high-risk applications

## 🔐 Security

- Environment variables for credentials
- API key rotation supported
- Encrypted connections to data warehouses
- Role-based access control for Airflow

## 📝 API Integration

### RazorpayX
```python
from src.ingestion.api_client import FintechAPIClient

client = FintechAPIClient()
transactions = client.get_razorpay_transactions(limit=100)
```

### Plaid
```python
client = FintechAPIClient()
transactions = client.get_plaid_transactions(
    access_token='your_token',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31)
)
```

## 🎓 Use Cases

1. **Real-time Loan Approval**: Instant risk assessment for loan applications
2. **Portfolio Monitoring**: Track default risk across loan portfolio
3. **Fraud Detection**: Identify suspicious patterns in real-time
4. **Credit Scoring**: Automated credit score calculation
5. **Regulatory Reporting**: Generate compliance reports


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.


## 🔮 Future Enhancements

- [ ] Add more ML models (XGBoost, Neural Networks)
- [ ] Implement A/B testing framework
- [ ] Add real-time alerting via email/SMS
- [ ] Integrate with more fintech APIs
- [ ] Add data quality checks with Great Expectations
- [ ] Implement data lineage tracking
- [ ] Add automated model retraining triggers
- [ ] Create mobile dashboard app
- [ ] Add explainability features (SHAP values)
- [ ] Implement distributed training with Spark MLlib

---
