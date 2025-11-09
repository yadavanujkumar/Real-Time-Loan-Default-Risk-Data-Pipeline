# Quick Start Guide

Get the Real-Time Loan Default Risk Pipeline running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- Git
- 4GB+ RAM available
- 10GB+ disk space

## Steps

### 1. Clone & Validate

```bash
# Clone repository
git clone https://github.com/yadavanujkumar/Real-Time-Loan-Default-Risk-Data-Pipeline.git
cd Real-Time-Loan-Default-Risk-Data-Pipeline

# Validate structure
python validate.py
```

Expected output: ✅ All validation checks passed!

### 2. Start Services

```bash
# Start all services (Kafka, Airflow, MLflow, etc.)
docker-compose up -d

# Wait for services to be ready (~30 seconds)
sleep 30

# Check all services are running
docker-compose ps
```

All services should show "Up" status.

### 3. Access Services

Open in your browser:

- **Airflow**: http://localhost:8080
  - Username: `airflow`
  - Password: `airflow`
  
- **MLflow**: http://localhost:5000

- **Dashboard**: http://localhost:8050

### 4. Run the Pipeline

#### Option A: Quick Demo (No Dependencies)

```bash
# Install only Python requirements
pip install pandas numpy scikit-learn mlflow

# Run with mock data
python main.py --mode full
```

This will:
- Generate sample loan data
- Process features
- Train ML model
- Save results

#### Option B: Full Pipeline (All Features)

```bash
# Install all dependencies
pip install -r requirements.txt

# Configure credentials
cp config/.env.template config/.env
# Edit config/.env with your API keys (optional)

# Run full pipeline
python main.py --mode full
```

### 5. View Dashboard

```bash
# Start dashboard
python main.py --mode dashboard
```

Open http://localhost:8050 to see:
- Risk distribution charts
- Default probability analysis
- Real-time metrics
- Time-series trends

## What You'll See

### Airflow UI
- DAG: `loan_default_risk_pipeline`
- Tasks: ingest → process → train → load → report
- Schedule: Every 6 hours

### MLflow UI
- Experiment: `loan-default-prediction`
- Metrics: accuracy, precision, recall, F1, ROC-AUC
- Models: Versioned and tracked

### Dashboard
- Total Applications
- Risk Categories (Low/Medium/High)
- Default Probability Distribution
- Debt-to-Income vs Default Probability
- Applications Over Time

## Testing

```bash
# Run all tests
pip install pytest pytest-cov
pytest tests/ -v

# Run specific test
pytest tests/test_feature_engineering.py -v
```

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Clean up
docker-compose down -v  # Warning: Deletes all data!
```

## Pipeline Modes

```bash
# Full pipeline
python main.py --mode full

# Batch processing only
python main.py --mode batch

# Stream processing (60 seconds)
python main.py --mode stream --duration 60

# Train model only
python main.py --mode train

# Dashboard only
python main.py --mode dashboard
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8080  # For Airflow
lsof -i :8050  # For Dashboard

# Kill process or change port in docker-compose.yml
```

### Services Not Starting
```bash
# Check Docker resources
docker stats

# View service logs
docker-compose logs kafka
docker-compose logs airflow-webserver
```

### Import Errors
```bash
# Make sure you're in the project directory
cd Real-Time-Loan-Default-Risk-Data-Pipeline

# Install dependencies
pip install -r requirements.txt
```

### No Data in Dashboard
```bash
# Generate sample data
python -c "
from src.processing.feature_engineering import RiskFeatureEngineer
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'customer_id': [f'c{i}' for i in range(100)],
    'loan_amount': np.random.uniform(5000, 50000, 100),
    'annual_income': np.random.uniform(30000, 120000, 100),
    'debt_amount': np.random.uniform(1000, 30000, 100),
    'employment_length': np.random.randint(0, 15, 100)
})

engineer = RiskFeatureEngineer()
df = engineer.create_all_features(df)
print(df.head())
"
```

## Next Steps

Once you've verified the basic setup:

1. **Configure Real APIs**: Edit `config/.env` with your fintech API keys
2. **Customize Features**: Modify `src/processing/feature_engineering.py`
3. **Add New Models**: Extend `src/models/loan_default_model.py`
4. **Deploy to Cloud**: Follow `docs/DEPLOYMENT.md`

## Getting Help

- **Documentation**: See `docs/` folder
- **Examples**: Check `docs/USAGE.md`
- **Architecture**: Read `docs/ARCHITECTURE.md`
- **Issues**: Open GitHub issue

## Quick Demo Script

```bash
#!/bin/bash
# demo.sh - Complete demo in one command

echo "🚀 Starting Real-Time Loan Default Risk Pipeline Demo..."

# Validate
echo "1️⃣ Validating project structure..."
python validate.py || exit 1

# Start services
echo "2️⃣ Starting Docker services..."
docker-compose up -d
sleep 30

# Run pipeline
echo "3️⃣ Running pipeline..."
pip install -q pandas numpy scikit-learn mlflow
python main.py --mode full

# Show results
echo "4️⃣ Pipeline complete! Access services:"
echo "   - Airflow: http://localhost:8080 (airflow/airflow)"
echo "   - MLflow: http://localhost:5000"
echo "   - Dashboard: http://localhost:8050"
echo ""
echo "5️⃣ Start dashboard with: python main.py --mode dashboard"
```

Save as `demo.sh`, make executable (`chmod +x demo.sh`), and run:

```bash
./demo.sh
```

## Success Criteria

You'll know it's working when:

✅ All Docker containers show "Up" status
✅ Airflow UI loads at localhost:8080
✅ MLflow shows experiment runs
✅ Dashboard displays charts
✅ No errors in `docker-compose logs`

---

**Time to Complete**: ~5 minutes
**Difficulty**: Beginner-friendly
**Support**: Available in documentation

Enjoy exploring the Real-Time Loan Default Risk Pipeline! 🎉
