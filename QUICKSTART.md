# Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

### Step 1: Install Docker & Docker Compose

```bash
# macOS (with Homebrew)
brew install docker docker-compose

# Ubuntu/Debian
sudo apt-get install docker.io docker-compose

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Clone and Navigate

```bash
git clone <repo-url>
cd analytics-platform
```

### Step 3: Start the Environment

```bash
# Start all services
docker-compose up -d

# Check status (wait 2-3 minutes for all services to start)
docker-compose ps

# Expected output:
# CONTAINER           STATUS
# analytics-postgres  Up (healthy)
# analytics-zookeeper Up
# analytics-kafka     Up
# analytics-spark-master  Up
# analytics-spark-worker  Up
# analytics-airflow-webserver  Up
# analytics-airflow-scheduler  Up
# analytics-api       Up
# forecasting-service Up
# anomaly-detection   Up
```

### Step 4: Test the APIs

```bash
# Analytics API
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"analytics-api"}

# Forecasting Service
curl http://localhost:8001/health
# Response: {"status":"healthy","service":"forecasting"}

# Anomaly Detection
curl http://localhost:8002/health
# Response: {"status":"healthy","service":"anomaly-detection"}
```

### Step 5: Access Dashboards

- **Airflow UI**: http://localhost:8080
  - Username: `airflow`
  - Password: `airflow`
  
- **Spark Master**: http://localhost:8080/
  
- **Prometheus Metrics**: http://localhost:9090

---

## 📊 Test Sample Data

### 1. Create Sample Orders

```bash
# Open Python terminal
python3

# Copy and run:
from kafka.producer import UnifiedProducer
from decimal import Decimal
from datetime import datetime

producer = UnifiedProducer(broker_urls=["localhost:9092"])

for i in range(10):
    order = {
        'order_id': 10000 + i,
        'customer_id': 1001,
        'product_id': 5001 + i,
        'supplier_id': 501,
        'order_date': datetime.now().isoformat(),
        'quantity': 2,
        'list_price': Decimal('99.99'),
        'order_amount': Decimal('199.98'),
        'total_amount': Decimal('219.98'),
        'cost_amount': Decimal('100.00'),
        'order_status': 'pending',
        'payment_status': 'pending'
    }
    producer.send_order_event(order)
    print(f"Sent order {order['order_id']}")

producer.flush()
producer.close()
```

### 2. Run Data Validation DAG

```bash
# Trigger via API
curl -X POST http://localhost:8080/api/v1/dags/data_validation/dagRuns

# Or via Airflow UI:
# 1. Go to http://localhost:8080
# 2. Find "data_validation" DAG
# 3. Click "Trigger DAG"
```

### 3. Check Results in Database

```bash
# Connect to PostgreSQL
psql postgresql://postgres:password@localhost:5432/analytics_warehouse

# List tables
\dt public.*

# Query orders
SELECT * FROM staging.stg_orders LIMIT 10;

# View KPI metrics
SELECT * FROM analytics.ecommerce_daily_metrics;
```

---

## 🔍 Query Examples

### E-Commerce Analytics

```bash
# Get revenue for last 30 days
curl "http://localhost:8000/ecommerce/metrics/2024-03-10/2024-04-10"

# Get conversion rate
curl "http://localhost:8000/ecommerce/conversion-rate?days=30"
```

### Supply Chain Analytics

```bash
# Get supplier performance
curl "http://localhost:8000/supply-chain/supplier/501/performance"

# Get delivery metrics
curl "http://localhost:8000/supply-chain/metrics/2024-03-10/2024-04-10"
```

### Financial Analytics

```bash
# Get budget vs actual
curl "http://localhost:8000/financial/budget-vs-actual/4000"

# Get financial metrics
curl "http://localhost:8000/financial/metrics/2024-03-10/2024-04-10"
```

### Forecasting

```bash
# Demand forecast for product 5001
curl "http://localhost:8001/forecast/demand/5001?horizon_days=30"

# Lead time forecast for supplier 501
curl "http://localhost:8001/forecast/lead-time/501"

# Cash flow forecast
curl "http://localhost:8001/forecast/cash-flow?horizon_days=30"
```

### Anomaly Detection

```bash
# Detect revenue anomaly
curl -X POST "http://localhost:8002/detect/ecommerce/revenue"

# Detect conversion rate anomaly
curl -X POST "http://localhost:8002/detect/ecommerce/conversion-rate"

# Get active alerts
curl "http://localhost:8002/alerts/active"
```

---

## 🔧 Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f analytics-api
docker-compose logs -f airflow-scheduler

# Follow real-time
docker-compose logs -f --tail=100
```

### Stop Services

```bash
# Stop all
docker-compose down

# Stop specific service
docker-compose stop analytics-api

# Stop and remove volumes (clean reset)
docker-compose down -v
```

### Rebuild Services

```bash
# Rebuild after code changes
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build analytics-api
```

### Access Database

```bash
# PostgreSQL CLI
docker exec -it analytics-postgres psql -U postgres -d analytics_warehouse

# Or use GUI client (e.g., DBeaver)
# Connection: localhost:5432, user: postgres, password: password
```

### View Kafka Topics

```bash
# List topics
docker exec analytics-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Consume messages from topic
docker exec analytics-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ecommerce.orders \
  --from-beginning
```

---

## 🚨 Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Service Not Starting

```bash
# Check logs
docker-compose logs analytics-postgres

# Verify docker is running
docker ps

# Restart service
docker-compose restart analytics-postgres
```

### Connection Refused

```bash
# Ensure all services are healthy
docker-compose ps

# Wait a bit longer (services take time to start)
sleep 30

# Test connectivity
curl http://localhost:8000/health
```

### Out of Memory

```bash
# Increase Docker memory limit
# Docker Desktop Settings → Resources → Memory

# Or use Docker Compose overrides
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

---

## 📚 Next Steps

1. **Review Architecture**: Read `PROJECT_GUIDE.md`
2. **Explore APIs**: Try the example curl commands above
3. **Check DAGs**: Visit Airflow UI to see scheduled jobs
4. **Monitor Metrics**: Check Prometheus at http://localhost:9090
5. **Modify Configuration**: Edit `config/config.yaml` for your needs
6. **Deploy to Production**: Follow deployment guide in `PROJECT_GUIDE.md`

---

## 🆘 Need Help?

- Check logs: `docker-compose logs <service>`
- Review `PROJECT_GUIDE.md` for detailed documentation
- Check Airflow logs: http://localhost:8080/admin/airflow/log
- Review error messages carefully
- Search GitHub issues

---

**Happy analyzing! 📊**
