"""Kafka producers and consumers for the Unified Enterprise Analytics Platform.

Provides:
    UnifiedProducer: Producer for all domain event topics.
    UnifiedConsumer: Single-topic consumer with batch support.
    MultiTopicConsumer: Consumer subscribing to multiple topics.
"""

from __future__ import annotations

from .consumer import MultiTopicConsumer, UnifiedConsumer
from .producer import UnifiedProducer

__all__ = [
    "UnifiedProducer",
    "UnifiedConsumer",
    "MultiTopicConsumer",
]
