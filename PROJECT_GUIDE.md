# Unified Enterprise Analytics & Operations Platform - Project Guide

## 📋 Overview

This is a **production-grade enterprise analytics platform** combining:
- **E-Commerce Analytics**: Order, inventory, and customer analytics
- **Supply Chain Optimization**: Supplier performance, delivery tracking, procurement costs
- **Financial Analytics**: Budget vs. actual, revenue forecasting, cash flow management

All three domains are unified into a single data warehouse with real-time and batch processing capabilities.

---

## 🏗️ Architecture

```
Data Sources (APIs, Databases, Event Streams)
         ↓
    [KAFKA] (Event Streaming)
     ↙ ↓ ↖
E-Commerce  Supply Chain  Financial Events
     ↖ ↓ ↙
[FLINK] (Real-Time Processing)
    ↓
[STAGING LAYER] (PostgreSQL)
    ↓
[AIRFLOW] (Orchestration & Scheduling)
    ↓
[PYSPARK] (ETL on EMR)
    ↓
[DATA WAREHOUSE] (PostgreSQL/Redshift)
   ├─ Dimensions (Products, Customers, Suppliers, GL Accounts)
   ├─ Facts (Orders, Deliveries, Transactions, Budgets)
   └─ Analytics Marts (KPI Aggregations)
    ↓
[MICROSERVICES] (EKS Deployment)
   ├─ Analytics API (REST endpoints for KPI queries)
   ├─ Forecasting Service (Demand, lead time, cash flow)
   └─ Anomaly Detection (Statistical anomaly detection)
    ↓
[DASHBOARDS & CLIENTS]
```

---

## 📁 Project Structure

```
├── config/
│   └── config.yaml                 # Central configuration file
│
├── data/
│   ├── models.py                   # Pydantic data models (all domains)
│   └── warehouse_schema.sql        # Data warehouse DDL
│
├── kafka/
│   ├── producer.py                 # Kafka event producers
│   └── consumer.py                 # Kafka event consumers
│
├── airflow/
│   └── dags/
│       ├── data_validation_dag.py  # Data quality checks
│       └── etl_batch_dag.py        # Daily batch ETL
│
├── spark/
│   ├── load_dimensions.py          # Load dimension tables
│   ├── load_facts.py               # Load fact tables
│   └── calculate_kpis.py           # Calculate KPI metrics
│
├── services/
│   ├── analytics_api.py            # REST API for analytics
│   ├── forecasting_service.py      # Demand/lead time/cash flow forecasting
│   └── anomaly_detection.py        # Statistical anomaly detection
│
├── k8s/
│   ├── namespace.yaml              # K8s namespace
│   ├── deployments.yaml            # Microservice deployments
│   ├── services.yaml               # K8s services
│   ├── ingress.yaml                # Ingress configuration
│   └── configmap.yaml              # ConfigMaps and Secrets
│
├── docker/
│   └── Dockerfile.services         # Docker image for microservices
│
├── docker-compose.yml              # Local development environment
├── requirements.txt                # Python dependencies
└── PROJECT_GUIDE.md               # This file
```

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose (for local development)
- Python 3.11+
- Kubernetes cluster (for production deployment)
- AWS credentials (for S3, EMR) - optional

### Option 1: Local Development with Docker Compose

```bash
# Clone the repository
git clone <repo-url>
cd analytics-platform

# Start all services
docker-compose up -d

# Wait for services to be healthy (2-3 minutes)
docker-compose ps

# Verify Airflow is running
open http://localhost:8080  # Airflow UI
open http://localhost:9090  # Prometheus (metrics)

# Verify Analytics API
curl http://localhost:8000/health
curl http://localhost:8001/health  # Forecasting
curl http://localhost:8002/health  # Anomaly Detection
```

### Option 2: Kubernetes Deployment

```bash
# Create namespace and deploy
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployments.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get pods -n analytics
kubectl get services -n analytics

# Port forward to test locally
kubectl port-forward -n analytics svc/analytics-api 8000:8000
curl http://localhost:8000/health
```

---

## 📊 Data Flow

### Event Ingestion (Real-Time)

1. **E-Commerce Events** → Kafka topic `ecommerce.orders`, `ecommerce.inventory`
   ```python
   from kafka.producer import UnifiedProducer
   
   producer = UnifiedProducer(broker_urls=["kafka:9092"])
   
   order = {
       'order_id': 12345,
       'customer_id': 1001,
       'product_id': 5001,
       'order_date': datetime.now(),
       'total_amount': Decimal('199.99'),
       ...
   }
   producer.send_order_event(order)
   ```

2. **Flink Processing** (Real-time anomaly detection, inventory alerts)
   - Stateful stream processing
   - Event-time semantics
   - Windowed aggregations

3. **Staging Tables** (PostgreSQL)
   - Store events for batch processing
   - Data quality checks

### Batch Processing (Daily)

1. **Airflow DAG Execution** (scheduled at 2 AM)
   - Data validation checks
   - Load dimensions from staging
   - Load facts from staging
   - Calculate daily KPIs
   - Refresh analytics marts

2. **PySpark Jobs** (EMR)
   - Transform and aggregate data
   - Dimensional modeling (SCD Type 2)
   - Cost calculations
   - Metric aggregations

3. **Data Warehouse** (PostgreSQL)
   - Fact and dimension tables
   - Analytics marts (pre-aggregated)
   - Audit and quality logs

### Analytics & Serving

1. **REST APIs** (Microservices on EKS)
   - Query KPIs
   - Generate forecasts
   - Detect anomalies

2. **Dashboards & Reports**
   - Executive summaries
   - Drill-down analytics
   - Real-time monitoring

---

## 🔌 API Endpoints

### Analytics API (Port 8000)

```bash
# E-Commerce KPIs
GET /ecommerce/metrics/{start_date}/{end_date}
GET /ecommerce/conversion-rate?days=30
GET /ecommerce/revenue-by-product

# Supply Chain KPIs
GET /supply-chain/metrics/{start_date}/{end_date}
GET /supply-chain/supplier/{supplier_id}/performance
GET /supply-chain/delivery-performance

# Financial KPIs
GET /financial/metrics/{start_date}/{end_date}
GET /financial/budget-vs-actual/{gl_account_id}
GET /financial/cash-flow

# Unified KPIs
GET /kpis/unified/{start_date}/{end_date}
GET /kpis/summary

# Health
GET /health
```

### Forecasting Service (Port 8001)

```bash
# Demand Forecasting
GET /forecast/demand/{product_id}?horizon_days=30
GET /forecast/demand/category/{category}?horizon_days=30

# Lead Time Forecasting
GET /forecast/lead-time/{supplier_id}

# Cash Flow Forecasting
GET /forecast/cash-flow?horizon_days=30

# Health
GET /health
```

### Anomaly Detection (Port 8002)

```bash
# Detect Anomalies
POST /detect/ecommerce/revenue
POST /detect/ecommerce/conversion-rate
POST /detect/supply-chain/on-time-delivery
POST /detect/financial/budget-variance

# Alerts
GET /alerts/active?severity=CRITICAL&domain=ecommerce
POST /alerts/{alert_id}/acknowledge

# Health
GET /health
```

---

## 💾 Database Schema

### Dimension Tables
- `dim_products` - Product catalog
- `dim_customers` - Customer master
- `dim_suppliers` - Supplier master
- `dim_gl_accounts` - Chart of accounts
- `dim_dates` - Date dimension (conformed)

### Fact Tables
- `fact_orders` - E-commerce orders
- `fact_deliveries` - Supply chain deliveries
- `fact_transactions` - Financial transactions
- `fact_budget_actuals` - Budget vs actual

### Analytics Marts (Aggregated)
- `analytics.ecommerce_daily_metrics`
- `analytics.supply_chain_daily_metrics`
- `analytics.financial_daily_metrics`
- `analytics.unified_kpi_metrics`

### Staging Tables
- `staging.stg_orders`
- `staging.stg_deliveries`
- `staging.stg_transactions`

---

## 🔧 Configuration

### config/config.yaml

Key configurations:
```yaml
kafka:
  broker_urls:
    - "localhost:9092"
  topics:
    ecommerce: [orders, inventory, customers]
    supply_chain: [suppliers, deliveries, purchase_orders]
    financials: [transactions, budgets, actuals]

database:
  warehouse:
    type: postgresql
    host: localhost
    port: 5432
    database: analytics_warehouse

airflow:
  schedules:
    data_validation: "0 0 * * *"  # Daily at midnight
    etl_batch: "0 2 * * *"        # Daily at 2 AM
    forecasting: "0 4 * * 0"      # Weekly at 4 AM

spark:
  master: "spark://localhost:7077"
  executor_memory: "4g"
  executors: 4
```

---

## 📈 Key Metrics (KPIs)

### E-Commerce
- **Conversion Rate** = Orders / Sessions
- **Cart Abandonment** = Abandoned Carts / Cart Additions
- **Average Order Value** = Total Revenue / Orders
- **Inventory Turnover** = COGS / Avg Inventory

### Supply Chain
- **On-Time Delivery %** = On-Time Deliveries / Total Deliveries
- **Average Lead Time** = Mean delivery days from order
- **Supplier Quality Score** = Quality Pass Rate %
- **Procurement Cost %** = Total Cost / Revenue

### Financial
- **Gross Margin %** = (Revenue - COGS) / Revenue
- **Operating Margin %** = Operating Income / Revenue
- **Budget Variance %** = (Actual - Budget) / Budget
- **Cash Conversion Cycle** = DIO + DSO - DPO

### Unified
- **Revenue per Supplier** = Total Revenue / Active Suppliers
- **Profit per Product** = Total Profit / Product Count
- **Order-to-Cash Cycle** = Average days from order to cash receipt
- **Inventory-to-Sales Ratio** = Inventory Value / Daily Sales

---

## 🚨 Anomaly Detection

### Statistical Methods
- **Z-Score**: Detect values >2σ from mean
- **Seasonal Decomposition**: Identify trend breaks
- **ARIMA Residuals**: Forecast deviations

### Example Alert
```json
{
  "alert_id": "ecom_revenue_2024-04-10",
  "severity": "CRITICAL",
  "domain": "ecommerce",
  "metric": "revenue",
  "current_value": 45000,
  "expected_value": 35000,
  "deviation_pct": 28.5,
  "z_score": 3.2,
  "recommendation": "Revenue up 28.5%. Check for system issues or special promotions."
}
```

---

## 📊 Forecasting Models

### Demand Forecasting
- **Method**: Linear Regression (simple) / ARIMA (advanced)
- **Horizon**: 7-365 days
- **Confidence**: Model R² score

### Lead Time Forecasting
- **Method**: Statistical averages by supplier
- **Horizon**: 7-30 days
- **Confidence**: Data consistency score

### Cash Flow Forecasting
- **Method**: Separate models for inflows/outflows
- **Horizon**: 7-90 days
- **Confidence**: Combined R² score

---

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Spark Jobs
```bash
# Test dimension loading
spark-submit spark/load_dimensions.py products

# Test fact loading
spark-submit spark/load_facts.py orders

# Test KPI calculation
spark-submit spark/calculate_kpis.py ecommerce
```

---

## 📝 Data Quality Checks

Automated checks in `airflow/dags/data_validation_dag.py`:
- ✓ Null values in critical columns
- ✓ Negative amounts validation
- ✓ Duplicate key detection
- ✓ Referential integrity
- ✓ Data type validation
- ✓ Range validation (e.g., lead time > 0)

---

## 🔐 Security

### Authentication & Authorization
- Database: SSL/TLS connections
- APIs: JWT tokens (future enhancement)
- Kubernetes: RBAC policies
- Secrets: Encrypted in Kubernetes

### Data Protection
- Passwords in environment variables (not in code)
- Sensitive fields encrypted at rest
- API rate limiting recommended

---

## 📊 Monitoring & Observability

### Metrics Collection
- **Prometheus** scrapes `/metrics` endpoints
- **Health checks** every 30 seconds
- **Performance monitoring** for long-running jobs

### Logging
- JSON-structured logs to stdout
- Centralized logging recommended (ELK stack)
- Log levels: DEBUG, INFO, WARNING, ERROR

### Alerting
- Anomaly detection service provides alerts
- Prometheus alerting rules
- Slack/email notifications (to implement)

---

## 🔄 Deployment Pipeline

### CI/CD (Recommended)
1. Push to GitHub → Trigger GitHub Actions
2. Run tests & linting
3. Build Docker image
4. Push to registry
5. Deploy to Kubernetes with Helm

### Manual Deployment
```bash
# Build and push image
docker build -f docker/Dockerfile.services -t your-registry/analytics-api:v1.0.0 .
docker push your-registry/analytics-api:v1.0.0

# Update Kubernetes deployment
kubectl set image deployment/analytics-api \
  analytics-api=your-registry/analytics-api:v1.0.0 \
  -n analytics
```

---

## 🛠️ Troubleshooting

### Service Healthy but Not Responding
```bash
# Check logs
docker logs <container-name>
kubectl logs -n analytics <pod-name>

# Test connectivity
curl -v http://localhost:8000/health
```

### Database Connection Issues
```bash
# Verify PostgreSQL is running
docker exec analytics-postgres psql -U postgres -c "SELECT version();"

# Check environment variables
docker exec <service> env | grep DATABASE_URL
```

### Spark Job Failures
```bash
# Check Spark logs
docker logs analytics-spark-master
docker logs analytics-spark-worker

# Submit job with verbose logging
spark-submit --verbose --conf spark.eventLog.enabled=true <job.py>
```

---

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [PySpark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [Kafka Python Client](https://kafka-python.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Official Docs](https://kubernetes.io/docs/)

---

## 📝 License

MIT License - See LICENSE file for details

---

## 📧 Support

For issues, feature requests, or questions:
- Create an issue on GitHub
- Contact the analytics team
- Review logs and troubleshooting guide

---

## ✅ Checklist for Production Deployment

- [ ] Configure production database credentials
- [ ] Set up secrets in Kubernetes
- [ ] Configure TLS/SSL for APIs
- [ ] Set up centralized logging (ELK/Splunk)
- [ ] Configure monitoring and alerting
- [ ] Set up backup strategy for database
- [ ] Configure auto-scaling policies
- [ ] Implement API rate limiting
- [ ] Set up disaster recovery plan
- [ ] Document runbook for operations team
- [ ] Conduct load testing
- [ ] Security audit and penetration testing
- [ ] Compliance review (GDPR, CCPA, etc.)

---

**Last Updated**: April 10, 2024
**Version**: 1.0.0
