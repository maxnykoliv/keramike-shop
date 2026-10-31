"""Order event names. Event payloads carry only ids; handlers read the current state themselves."""

ORDER_CREATED = "order.created"
ORDER_STATUS_CHANGED = "order.status_changed"
ORDER_CANCELLED = "order.cancelled"
ORDER_PAID = "order.paid"
ORDER_REFUNDED = "order.refunded"
ORDER_PAYMENT_MISMATCH = "order.payment_mismatch"
ORDER_UNCONFIRMED_REMINDER = "order.unconfirmed_reminder"
