ORDERS = {
    "ORD-123456": {
        "order_id": "ORD-123456",
        "status": "shipped",
    },
    "ORD-654321": {
        "order_id": "ORD-654321",
        "status": "processing",
    },
}


def lookup_order(order_id: str) -> dict:
    """Return the current status of an order by its order ID."""

    return ORDERS.get(
        order_id,
        {
            "order_id": order_id,
            "status": "not_found",
        },
    )