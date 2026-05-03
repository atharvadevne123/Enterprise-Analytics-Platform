"""
Kafka Producers for all domains
Handles real-time event streaming to Kafka topics
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from kafka import KafkaProducer

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class UnifiedProducer:
    """Unified Kafka producer for all domains"""

    def __init__(self, broker_urls: Optional[List[str]] = None) -> None:
        """Initialize Kafka producer.

        Args:
            broker_urls: List of Kafka broker addresses.
        """
        if broker_urls is None:
            broker_urls = ["localhost:9092"]

        self.broker_urls = broker_urls
        self.producer = KafkaProducer(
            bootstrap_servers=broker_urls,
            value_serializer=lambda v: json.dumps(v, cls=DecimalEncoder).encode('utf-8'),
            acks='all',
            retries=3,
            compression_type='gzip',
            linger_ms=100,
            batch_size=16384
        )
        logger.info(f"Kafka producer initialized with brokers: {broker_urls}")

    def send_order_event(self, order_data: Dict[str, Any], callback=None) -> bool:
        """Send order event to ecommerce.orders topic"""
        try:
            future = self.producer.send(
                'ecommerce.orders',
                value=order_data,
                key=str(order_data.get('order_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"Order event send failed: {e}"))

            logger.debug(f"Order event sent: {order_data.get('order_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send order event: {e}")
            return False

    def send_inventory_event(self, inventory_data: Dict[str, Any], callback=None) -> bool:
        """Send inventory event to ecommerce.inventory topic"""
        try:
            future = self.producer.send(
                'ecommerce.inventory',
                value=inventory_data,
                key=str(inventory_data.get('product_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"Inventory event send failed: {e}"))

            logger.debug(f"Inventory event sent: {inventory_data.get('product_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send inventory event: {e}")
            return False

    def send_customer_event(self, customer_data: Dict[str, Any], callback=None) -> bool:
        """Send customer event to ecommerce.customers topic"""
        try:
            future = self.producer.send(
                'ecommerce.customers',
                value=customer_data,
                key=str(customer_data.get('customer_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"Customer event send failed: {e}"))

            logger.debug(f"Customer event sent: {customer_data.get('customer_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send customer event: {e}")
            return False

    def send_delivery_event(self, delivery_data: Dict[str, Any], callback=None) -> bool:
        """Send delivery event to supply_chain.deliveries topic"""
        try:
            future = self.producer.send(
                'supply_chain.deliveries',
                value=delivery_data,
                key=str(delivery_data.get('delivery_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"Delivery event send failed: {e}"))

            logger.debug(f"Delivery event sent: {delivery_data.get('delivery_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send delivery event: {e}")
            return False

    def send_purchase_order_event(self, po_data: Dict[str, Any], callback=None) -> bool:
        """Send purchase order event to supply_chain.purchase_orders topic"""
        try:
            future = self.producer.send(
                'supply_chain.purchase_orders',
                value=po_data,
                key=str(po_data.get('po_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"PO event send failed: {e}"))

            logger.debug(f"Purchase order event sent: {po_data.get('po_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send purchase order event: {e}")
            return False

    def send_supplier_event(self, supplier_data: Dict[str, Any], callback=None) -> bool:
        """Send supplier event to supply_chain.suppliers topic"""
        try:
            future = self.producer.send(
                'supply_chain.suppliers',
                value=supplier_data,
                key=str(supplier_data.get('supplier_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"Supplier event send failed: {e}"))

            logger.debug(f"Supplier event sent: {supplier_data.get('supplier_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send supplier event: {e}")
            return False

    def send_transaction_event(self, transaction_data: Dict[str, Any], callback=None) -> bool:
        """Send transaction event to financials.transactions topic"""
        try:
            future = self.producer.send(
                'financials.transactions',
                value=transaction_data,
                key=str(transaction_data.get('transaction_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"Transaction event send failed: {e}"))

            logger.debug(f"Transaction event sent: {transaction_data.get('transaction_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send transaction event: {e}")
            return False

    def send_budget_event(self, budget_data: Dict[str, Any], callback=None) -> bool:
        """Send budget event to financials.budgets topic"""
        try:
            future = self.producer.send(
                'financials.budgets',
                value=budget_data,
                key=str(budget_data.get('budget_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"Budget event send failed: {e}"))

            logger.debug(f"Budget event sent: {budget_data.get('budget_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send budget event: {e}")
            return False

    def send_actual_event(self, actual_data: Dict[str, Any], callback=None) -> bool:
        """Send actual event to financials.actuals topic"""
        try:
            future = self.producer.send(
                'financials.actuals',
                value=actual_data,
                key=str(actual_data.get('actual_id')).encode('utf-8')
            )

            if callback:
                future.add_callback(callback)
                future.add_errback(lambda e: logger.error(f"Actual event send failed: {e}"))

            logger.debug(f"Actual event sent: {actual_data.get('actual_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send actual event: {e}")
            return False

    def flush(self, timeout_ms: int = 30000):
        """Flush all pending messages"""
        self.producer.flush(timeout_ms=timeout_ms)
        logger.info("Producer flushed successfully")

    def send_financial_event(self, financial_data: Dict[str, Any], callback: Any = None) -> bool:
        """Alias for send_transaction_event for backward compatibility."""
        return self.send_transaction_event(financial_data, callback)

    def close(self) -> None:
        """Close the producer."""
        self.producer.close()
        logger.info("Producer closed")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    producer = UnifiedProducer()

    # Example order event
    sample_order = {
        'order_id': 12345,
        'customer_id': 1001,
        'product_id': 5001,
        'supplier_id': 501,
        'order_date': datetime.utcnow().isoformat(),
        'quantity': 2,
        'list_price': Decimal('99.99'),
        'order_amount': Decimal('199.98'),
        'total_amount': Decimal('219.98'),
        'cost_amount': Decimal('100.00'),
        'order_status': 'pending',
        'payment_status': 'pending'
    }

    producer.send_order_event(sample_order)
    producer.flush()
    producer.close()
