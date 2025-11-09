# Architecture Documentation

## System Architecture

### Overview
The Real-Time Loan Default Risk Pipeline is a distributed data engineering system designed to process and analyze loan application and transaction data in real-time, providing instant risk assessments and credit analysis.

## Components

### 1. Data Ingestion Layer

#### API Clients
- **Purpose**: Fetch data from fintech APIs (RazorpayX, Plaid)
- **Implementation**: `src/ingestion/api_client.py`
- **Features**:
  - REST API integration
  - Rate limiting and retry logic
  - Mock data generation for testing
  - Error handling and logging

#### Kafka Producer
- **Purpose**: Stream data into Kafka topics
- **Implementation**: `src/ingestion/kafka_producer.py`
- **Topics**:
  - `loan-applications`: New loan applications
  - `transactions`: Financial transactions
  - `repayments`: Loan repayments
- **Features**:
  - Batch sending
  - Message serialization
  - Acknowledgment handling

#### Kafka Consumer
- **Purpose**: Consume streaming data from Kafka
- **Implementation**: `src/ingestion/kafka_consumer.py`
- **Features**:
  - Auto-commit or manual commit
  - Consumer group management
  - Batch processing support

### 2. Processing Layer

#### Stream Processor
- **Purpose**: Real-time data processing with Spark Structured Streaming
- **Implementation**: `src/processing/stream_processor.py`
- **Capabilities**:
  - Kafka stream reading
  - Schema enforcement
  - Windowed aggregations
  - Join operations
  - Checkpoint management

#### Feature Engineering
- **Purpose**: Calculate risk metrics and features
- **Implementation**: `src/processing/feature_engineering.py`
- **Features Computed**:
  - Debt-to-Income Ratio
  - Loan-to-Value Ratio
  - Credit Utilization
  - Payment Delay Metrics
  - Income Stability Score
  - Default Probability

### 3. Storage Layer

#### Data Lake (S3)
- **Purpose**: Raw and processed data storage
- **Structure**:
  ```
  bucket/
  ├── raw/
  │   ├── loan_applications.parquet
  │   └── transactions.parquet
  ├── processed/
  │   └── loan_features_YYYYMMDD.parquet
  └── models/
      └── loan_default_model_YYYYMMDD.pkl
  ```

#### Data Warehouse (Snowflake/BigQuery)
- **Purpose**: Analytical queries and reporting
- **Tables**:
  - `loan_risk_features`: Processed features
  - `loan_applications`: Application data
  - `transactions`: Transaction history
  - `repayments`: Repayment records

### 4. ML Layer

#### Model Training
- **Purpose**: Train ML models for default prediction
- **Implementation**: `src/models/loan_default_model.py`
- **Algorithms**:
  - Random Forest Classifier
  - Gradient Boosting Classifier
  - Logistic Regression
- **Features**:
  - Cross-validation
  - Hyperparameter tuning
  - Model versioning with MLflow
  - Feature importance analysis

#### Model Serving
- **Purpose**: Real-time predictions
- **Approach**: Batch scoring or real-time API
- **Integration**: MLflow model registry

### 5. Orchestration Layer

#### Airflow DAGs
- **Purpose**: Schedule and orchestrate pipeline tasks
- **Implementation**: `src/orchestration/loan_risk_dag.py`
- **Schedule**: Every 6 hours
- **Tasks**:
  1. API data ingestion
  2. Feature processing
  3. Model training
  4. Data warehouse loading
  5. Report generation

### 6. Visualization Layer

#### Real-time Dashboard
- **Purpose**: Monitor risk metrics in real-time
- **Implementation**: `dashboards/risk_dashboard.py`
- **Technology**: Dash + Plotly
- **Features**:
  - Auto-refresh (30 seconds)
  - Risk distribution charts
  - Default probability histograms
  - Time-series analysis
  - Interactive filters

## Data Flow

### Real-time Flow
```
Fintech API → Kafka Producer → Kafka Topic → Spark Streaming → 
Feature Engineering → S3/Warehouse → Dashboard
```

### Batch Flow
```
Scheduled Airflow DAG → API Client → Data Processing → 
Feature Engineering → Model Training → Data Warehouse → Reports
```

### Prediction Flow
```
New Application → Feature Engineering → ML Model → 
Risk Score → Dashboard/Alert
```

## Technology Stack

### Data Processing
- **Apache Spark**: Distributed stream processing
- **PySpark**: Python API for Spark
- **Pandas**: Data manipulation
- **NumPy**: Numerical computing

### Messaging & Streaming
- **Apache Kafka**: Event streaming platform
- **Confluent Kafka**: Python Kafka client

### Storage
- **AWS S3**: Object storage
- **Snowflake**: Cloud data warehouse
- **Google BigQuery**: Alternative data warehouse

### ML/AI
- **Scikit-learn**: Machine learning models
- **MLflow**: ML lifecycle management
- **Joblib**: Model serialization

### Orchestration
- **Apache Airflow**: Workflow orchestration
- **Docker Compose**: Container orchestration

### Visualization
- **Dash**: Web application framework
- **Plotly**: Interactive charts
- **Streamlit**: Alternative dashboard (optional)

### Development
- **Python 3.10+**: Primary language
- **pytest**: Testing framework
- **Black**: Code formatting
- **Flake8**: Linting

## Scalability Considerations

### Horizontal Scaling
- **Kafka**: Add more partitions and consumers
- **Spark**: Increase cluster size
- **Airflow**: Add more workers

### Vertical Scaling
- **Increase resources** per component
- **Optimize queries** for warehouses
- **Cache frequently accessed data**

### Performance Optimization
- **Partitioning**: Data partitioned by date
- **Compression**: Use Parquet with Snappy
- **Batch sizes**: Tuned for throughput
- **Checkpointing**: Enable for fault tolerance

## Security

### Authentication
- API keys for fintech APIs
- AWS IAM roles for S3
- Service accounts for GCP/BigQuery
- Username/password for Snowflake

### Encryption
- TLS/SSL for API communications
- Encrypted connections to warehouses
- Encrypted S3 buckets

### Access Control
- Role-based access in Airflow
- IAM policies in AWS
- Fine-grained access in Snowflake/BigQuery

## Monitoring & Logging

### Application Logs
- JSON-formatted logs
- Centralized in `/logs` directory
- Log rotation enabled

### Metrics
- Kafka lag monitoring
- Spark job metrics
- Model performance metrics
- API response times

### Alerting
- Email alerts for DAG failures
- Slack integration (optional)
- PagerDuty integration (optional)

## Disaster Recovery

### Backups
- S3 versioning enabled
- Database backups (Snowflake/BigQuery)
- Model registry backups (MLflow)

### Fault Tolerance
- Kafka replication
- Spark checkpointing
- Airflow task retries
- Database transactions

### Recovery Procedures
1. Restore from S3 backups
2. Replay Kafka messages
3. Reprocess failed batches
4. Retrain models if needed

## Future Enhancements

1. **Real-time Model Serving**: Deploy models as REST APIs
2. **Feature Store**: Centralized feature repository
3. **Data Quality**: Integrate Great Expectations
4. **A/B Testing**: Compare model versions
5. **AutoML**: Automated model selection
6. **Explainability**: SHAP/LIME integration
7. **Multi-region**: Deploy across regions
8. **Real-time Alerts**: SMS/Email notifications
