# Deployment Guide

## Prerequisites

Before deploying the Real-Time Loan Default Risk Pipeline, ensure you have:

1. **Python 3.8+** installed
2. **Docker** and **Docker Compose** installed
3. **Git** for version control
4. **Cloud accounts** (choose at least one):
   - AWS account (for S3)
   - GCP account (for BigQuery)
   - Snowflake account (for data warehouse)
5. **API credentials** (optional, for real data):
   - RazorpayX API keys
   - Plaid API credentials

## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yadavanujkumar/Real-Time-Loan-Default-Risk-Data-Pipeline.git
cd Real-Time-Loan-Default-Risk-Data-Pipeline
```

### 2. Validate Project Structure
```bash
python validate.py
```

### 3. Run Setup Script
```bash
./setup.sh
```

Or manually:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp config/.env.template config/.env
# Edit config/.env with your credentials
```

### 4. Configure Environment Variables
Edit `config/.env`:
```bash
# AWS credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Snowflake (optional)
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password

# GCP (optional)
GCP_PROJECT_ID=your_project_id
GCP_CREDENTIALS_PATH=/path/to/credentials.json

# Fintech APIs (optional)
RAZORPAY_KEY_ID=your_key
RAZORPAY_KEY_SECRET=your_secret
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
```

### 5. Start Services with Docker Compose
```bash
docker-compose up -d
```

This starts:
- Kafka + Zookeeper
- PostgreSQL (for Airflow)
- Airflow (webserver + scheduler)
- MLflow tracking server
- Application container
- Dashboard

### 6. Verify Services
```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f
```

Access the services:
- **Airflow UI**: http://localhost:8080 (airflow/airflow)
- **MLflow UI**: http://localhost:5000
- **Dashboard**: http://localhost:8050

## Running the Pipeline

### Option 1: Full Pipeline
```bash
python main.py --mode full
```

### Option 2: Individual Components

#### Batch Processing
```bash
python main.py --mode batch
```

#### Stream Processing (60 seconds)
```bash
python main.py --mode stream --duration 60
```

#### Model Training
```bash
python main.py --mode train
```

#### Dashboard Only
```bash
python main.py --mode dashboard
```

## Production Deployment

### AWS Deployment

#### 1. Setup Infrastructure
```bash
# Create S3 bucket
aws s3 mb s3://loan-risk-data

# Create IAM role with S3 access
# Create EC2 instance or use ECS
```

#### 2. Deploy Application
```bash
# Build Docker image
docker build -t loan-risk-pipeline:latest .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag loan-risk-pipeline:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/loan-risk-pipeline:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/loan-risk-pipeline:latest
```

#### 3. Setup Managed Services
- **MSK** (Managed Kafka) for streaming
- **MWAA** (Managed Airflow) for orchestration
- **RDS** for metadata storage
- **ECS/EKS** for container orchestration

### GCP Deployment

#### 1. Setup Infrastructure
```bash
# Create GCS bucket
gsutil mb gs://loan-risk-data

# Create BigQuery dataset
bq mk loan_risk_dataset
```

#### 2. Deploy to Cloud Run
```bash
# Build and push
gcloud builds submit --tag gcr.io/<project-id>/loan-risk-pipeline

# Deploy
gcloud run deploy loan-risk-pipeline \
  --image gcr.io/<project-id>/loan-risk-pipeline \
  --platform managed \
  --region us-central1
```

#### 3. Setup Managed Services
- **Pub/Sub** for messaging
- **Dataflow** for stream processing
- **Cloud Composer** for Airflow
- **GKE** for Kubernetes

### Kubernetes Deployment

#### 1. Create Kubernetes Manifests
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: loan-risk-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: loan-risk
  template:
    metadata:
      labels:
        app: loan-risk
    spec:
      containers:
      - name: pipeline
        image: loan-risk-pipeline:latest
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
```

#### 2. Deploy
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Monitoring Setup

### 1. Prometheus + Grafana
```bash
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

### 2. ELK Stack (Elasticsearch, Logstash, Kibana)
```bash
# For centralized logging
docker-compose -f docker-compose-elk.yml up -d
```

### 3. CloudWatch / Stackdriver
- Configure for cloud deployments
- Set up alarms and dashboards

## Scaling Considerations

### Horizontal Scaling
1. **Kafka**: Increase partitions
   ```bash
   kafka-topics.sh --alter --topic loan-applications --partitions 10
   ```

2. **Spark**: Add more worker nodes
   ```yaml
   spark:
     worker:
       replicas: 5
   ```

3. **Airflow**: Add more workers
   ```bash
   docker-compose scale airflow-worker=5
   ```

### Vertical Scaling
- Increase container resources
- Optimize Spark configurations
- Tune database parameters

## Backup and Recovery

### 1. Data Backup
```bash
# Backup S3 data
aws s3 sync s3://loan-risk-data s3://loan-risk-data-backup

# Export BigQuery tables
bq extract dataset.table gs://backup/table.csv
```

### 2. Database Backup
```bash
# PostgreSQL
docker exec postgres pg_dump -U airflow > backup.sql
```

### 3. Configuration Backup
```bash
# Backup configs
tar -czf configs-backup.tar.gz config/
```

## Troubleshooting

### Common Issues

#### 1. Kafka Connection Error
```bash
# Check Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka

# Test connection
kafka-topics.sh --list --bootstrap-server localhost:9092
```

#### 2. Airflow DAG Not Showing
```bash
# Check DAG syntax
python src/orchestration/loan_risk_dag.py

# Refresh DAGs
docker-compose restart airflow-scheduler
```

#### 3. Dashboard Not Loading
```bash
# Check application logs
docker-compose logs loan-risk-app

# Check if port is available
netstat -an | grep 8050
```

#### 4. Model Training Fails
```bash
# Check MLflow
curl http://localhost:5000/health

# Check data availability
python -c "from src.storage.connectors import S3Connector; S3Connector().list_objects()"
```

## Performance Tuning

### Spark Configuration
```python
# In config.yaml
spark:
  executor_memory: "4g"
  executor_cores: 4
  driver_memory: "2g"
```

### Kafka Configuration
```yaml
kafka:
  num.partitions: 10
  replication.factor: 3
  batch.size: 16384
```

### Database Optimization
```sql
-- Create indexes for faster queries
CREATE INDEX idx_customer_id ON loan_risk_features(customer_id);
CREATE INDEX idx_timestamp ON loan_risk_features(application_timestamp);
```

## Security Hardening

### 1. Enable SSL/TLS
```yaml
# For Kafka
ssl.enabled: true
ssl.keystore.location: /path/to/keystore
```

### 2. Implement Authentication
```python
# For APIs
from flask import Flask, request
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return {'error': 'Unauthorized'}, 401
        return f(*args, **kwargs)
    return decorated
```

### 3. Network Security
```bash
# Use VPC/private networks
# Configure security groups
# Enable firewall rules
```

## Maintenance

### Regular Tasks
1. **Daily**: Monitor logs and metrics
2. **Weekly**: Review model performance
3. **Monthly**: Update dependencies
4. **Quarterly**: Security audits

### Update Dependencies
```bash
pip list --outdated
pip install --upgrade <package>
```

### Rotate Credentials
```bash
# Update .env with new credentials
# Restart services
docker-compose restart
```

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review logs in `logs/`
3. Open GitHub issue
4. Contact: yadavanujkumar@example.com

---

**Last Updated**: 2024-01-09
