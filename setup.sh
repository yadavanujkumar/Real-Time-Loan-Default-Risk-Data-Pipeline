#!/bin/bash
# Setup script for Real-Time Loan Default Risk Pipeline

set -e

echo "=========================================="
echo "Setting up Loan Default Risk Pipeline"
echo "=========================================="

# Create necessary directories
echo "Creating directories..."
mkdir -p logs data/raw data/processed data/models

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Setup config
if [ ! -f "config/.env" ]; then
    echo "Creating .env file from template..."
    cp config/.env.template config/.env
    echo "Please edit config/.env with your credentials"
fi

# Create Kafka topics (if Kafka is running)
echo "Checking if Kafka is available..."
if command -v kafka-topics.sh &> /dev/null; then
    echo "Creating Kafka topics..."
    kafka-topics.sh --create --topic loan-applications --bootstrap-server localhost:9092 --if-not-exists || true
    kafka-topics.sh --create --topic transactions --bootstrap-server localhost:9092 --if-not-exists || true
    kafka-topics.sh --create --topic repayments --bootstrap-server localhost:9092 --if-not-exists || true
else
    echo "Kafka not found. Topics will be auto-created when Kafka starts."
fi

# Initialize Airflow database (if Airflow is installed)
if command -v airflow &> /dev/null; then
    echo "Initializing Airflow database..."
    export AIRFLOW_HOME=$(pwd)/airflow
    airflow db init || true
fi

echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config/.env with your credentials"
echo "2. Start services: docker-compose up -d"
echo "3. Run pipeline: python main.py --mode full"
echo "4. Access dashboard: http://localhost:8050"
echo ""
echo "For more information, see README.md"
