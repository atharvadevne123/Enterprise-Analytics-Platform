"""Tests for the messaging package public interface."""

from __future__ import annotations

import pytest


class TestMessagingPackageExports:
    def test_unified_producer_exported(self):
        from messaging import UnifiedProducer

        assert UnifiedProducer is not None

    def test_unified_consumer_exported(self):
        from messaging import UnifiedConsumer

        assert UnifiedConsumer is not None

    def test_multi_topic_consumer_exported(self):
        from messaging import MultiTopicConsumer

        assert MultiTopicConsumer is not None

    def test_all_defined_in_dunder_all(self):
        import messaging

        assert "UnifiedProducer" in messaging.__all__
        assert "UnifiedConsumer" in messaging.__all__
        assert "MultiTopicConsumer" in messaging.__all__

    def test_package_has_docstring(self):
        import messaging

        assert messaging.__doc__ is not None
        assert len(messaging.__doc__) > 10

    @pytest.mark.parametrize("name", ["UnifiedProducer", "UnifiedConsumer", "MultiTopicConsumer"])
    def test_all_classes_are_importable_by_name(self, name):
        import messaging

        cls = getattr(messaging, name)
        assert cls is not None
        assert callable(cls)


class TestMessagingClassAttributes:
    def test_producer_has_send_order_event(self):
        from messaging import UnifiedProducer

        assert hasattr(UnifiedProducer, "send_order_event")

    def test_producer_has_send_delivery_event(self):
        from messaging import UnifiedProducer

        assert hasattr(UnifiedProducer, "send_delivery_event")

    def test_producer_has_close_method(self):
        from messaging import UnifiedProducer

        assert hasattr(UnifiedProducer, "close")

    def test_consumer_has_consume_messages(self):
        from messaging import UnifiedConsumer

        assert hasattr(UnifiedConsumer, "consume_messages")

    def test_consumer_has_close_method(self):
        from messaging import UnifiedConsumer

        assert hasattr(UnifiedConsumer, "close")

    def test_multi_topic_consumer_has_consume_messages(self):
        from messaging import MultiTopicConsumer

        assert hasattr(MultiTopicConsumer, "consume_messages")
