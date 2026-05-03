"""
Data models for the Unified Enterprise Analytics Platform
Defines Pydantic models for all events and data structures
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

# ============================================================================
# ENUMS
# ============================================================================

class OrderStatus(str, Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class TransactionType(str, Enum):
    JOURNAL_ENTRY = "journal_entry"
    INVOICE = "invoice"
    PAYMENT = "payment"
    CREDIT_MEMO = "credit_memo"
    DEBIT_MEMO = "debit_memo"


class CustomerSegment(str, Enum):
    VIP = "vip"
    REGULAR = "regular"
    NEW = "new"
    INACTIVE = "inactive"


# ============================================================================
# E-COMMERCE MODELS
# ============================================================================

class Product(BaseModel):
    product_id: int
    product_name: str
    category: str
    subcategory: Optional[str] = None
    supplier_id: int
    cost: Decimal
    list_price: Decimal
    current_stock_level: int = 0
    reorder_point: int = 100
    lead_time_days: int
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class Customer(BaseModel):
    customer_id: int
    customer_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    segment: CustomerSegment = CustomerSegment.REGULAR
    lifetime_value: Decimal = Decimal("0.00")
    country: Optional[str] = None
    region: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class OrderEvent(BaseModel):
    """Order event from e-commerce system (Kafka topic: ecommerce.orders)"""
    order_id: int
    customer_id: int
    product_id: int
    supplier_id: Optional[int] = None
    order_date: datetime
    quantity: int
    list_price: Decimal
    discount_amount: Decimal = Decimal("0.00")
    order_amount: Decimal
    tax_amount: Decimal = Decimal("0.00")
    shipping_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    cost_amount: Decimal
    order_status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    shipping_status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class InventoryEvent(BaseModel):
    """Inventory update event (Kafka topic: ecommerce.inventory)"""
    product_id: int
    stock_level: int
    previous_level: int
    change_quantity: int
    change_reason: str  # Purchase, Sale, Adjustment, Damage
    warehouse_id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


# ============================================================================
# SUPPLY CHAIN MODELS
# ============================================================================

class Supplier(BaseModel):
    supplier_id: int
    supplier_name: str
    country: str
    region: Optional[str] = None
    on_time_delivery_pct: Decimal = Decimal("0.00")
    quality_score: Decimal = Decimal("0.00")
    lead_time_days: int
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    is_active: bool = True
    payment_terms: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class PurchaseOrderEvent(BaseModel):
    """Purchase order event (Kafka topic: supply_chain.purchase_orders)"""
    po_id: int
    supplier_id: int
    product_id: int
    quantity: int
    unit_cost: Decimal
    total_cost: Decimal
    order_date: datetime
    expected_delivery_date: datetime
    po_status: str  # Draft, Sent, Confirmed, Received, Cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class DeliveryEvent(BaseModel):
    """Delivery event from suppliers (Kafka topic: supply_chain.deliveries)"""
    delivery_id: int
    po_id: int
    supplier_id: int
    product_id: int
    quantity_ordered: int
    quantity_delivered: int
    quantity_rejected: int = 0
    unit_cost: Decimal
    total_cost: Decimal
    order_date: datetime
    delivery_date: datetime
    promised_date: datetime
    lead_time_days: int
    is_on_time: bool
    is_quality_pass: bool = True
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


# ============================================================================
# FINANCIAL MODELS
# ============================================================================

class GLAccount(BaseModel):
    gl_account_id: str
    account_name: str
    account_type: str  # Asset, Liability, Equity, Revenue, Expense
    account_subtype: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    is_balance_sheet: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionEvent(BaseModel):
    """Financial transaction event (Kafka topic: financials.transactions)"""
    transaction_id: int
    gl_account_id: str
    debit_amount: Decimal = Decimal("0.00")
    credit_amount: Decimal = Decimal("0.00")
    net_amount: Decimal
    transaction_type: TransactionType
    description: Optional[str] = None
    reference_id: Optional[str] = None  # Order ID, PO ID, Invoice ID
    currency_code: str = "USD"
    exchange_rate: Decimal = Decimal("1.0")
    is_intercompany: bool = False
    transaction_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class BudgetEvent(BaseModel):
    """Budget event (Kafka topic: financials.budgets)"""
    budget_id: int
    gl_account_id: str
    budget_amount: Decimal
    budget_type: str  # Monthly, Quarterly, Annual
    budget_version: int
    budget_year: int
    budget_month: Optional[int] = None
    budget_quarter: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class ActualEvent(BaseModel):
    """Actual financial event (Kafka topic: financials.actuals)"""
    actual_id: int
    gl_account_id: str
    actual_amount: Decimal
    transaction_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


# ============================================================================
# KPI AND METRICS MODELS
# ============================================================================

class ECommerceMetrics(BaseModel):
    """Daily e-commerce KPI metrics"""
    date: datetime
    total_orders: int
    total_customers: int
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    average_order_value: Decimal
    conversion_rate: Decimal  # percentage
    cart_abandonment_rate: Decimal  # percentage
    inventory_turnover: Decimal
    returned_orders: int = 0
    refunded_amount: Decimal = Decimal("0.00")

    class Config:
        json_encoders = {Decimal: str}


class SupplyChainMetrics(BaseModel):
    """Daily supply chain KPI metrics"""
    date: datetime
    total_deliveries: int
    on_time_deliveries: int
    on_time_delivery_pct: Decimal
    total_procurement_cost: Decimal
    average_lead_time_days: Decimal
    supplier_quality_score: Decimal
    cancelled_orders: int = 0
    delayed_deliveries: int = 0

    class Config:
        json_encoders = {Decimal: str}


class FinancialMetrics(BaseModel):
    """Daily financial KPI metrics"""
    date: datetime
    total_revenue: Decimal
    total_expense: Decimal
    net_income: Decimal
    budget_variance: Decimal
    cash_position: Decimal
    gross_margin_pct: Decimal
    operating_margin_pct: Decimal
    accounts_receivable: Decimal = Decimal("0.00")
    accounts_payable: Decimal = Decimal("0.00")

    class Config:
        json_encoders = {Decimal: str}


class UnifiedKPIMetrics(BaseModel):
    """Unified cross-domain KPI metrics"""
    date: datetime
    revenue_per_supplier: Decimal
    profit_per_product: Decimal
    order_to_cash_cycle_days: int
    inventory_to_sales_ratio: Decimal
    cash_conversion_cycle_days: int
    return_rate_pct: Decimal = Decimal("0.00")
    supplier_performance_score: Decimal = Decimal("0.00")

    class Config:
        json_encoders = {Decimal: str}


# ============================================================================
# ANOMALY DETECTION MODELS
# ============================================================================

class AnomalyAlert(BaseModel):
    """Anomaly detected in metrics"""
    alert_id: str
    severity: str  # CRITICAL, WARNING, INFO
    domain: str  # ecommerce, supply_chain, financial
    metric_name: str
    current_value: Decimal
    expected_range_min: Decimal
    expected_range_max: Decimal
    deviation_pct: Decimal
    root_cause: Optional[str] = None
    recommended_action: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False

    class Config:
        json_encoders = {Decimal: str}


# ============================================================================
# FORECAST MODELS
# ============================================================================

class DemandForecast(BaseModel):
    """Product demand forecast"""
    forecast_id: str
    product_id: int
    forecast_date: datetime
    forecast_horizon_days: int
    forecasted_quantity: Decimal
    confidence_level: Decimal  # 0.0 to 1.0
    model_version: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class LeadTimeForecast(BaseModel):
    """Supplier lead time forecast"""
    forecast_id: str
    supplier_id: int
    forecast_date: datetime
    forecasted_lead_time_days: int
    confidence_level: Decimal
    model_version: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}


class CashFlowForecast(BaseModel):
    """Financial cash flow forecast"""
    forecast_id: str
    forecast_date: datetime
    forecast_horizon_days: int
    forecasted_cash_inflow: Decimal
    forecasted_cash_outflow: Decimal
    net_cash_flow: Decimal
    confidence_level: Decimal
    model_version: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {Decimal: str}
