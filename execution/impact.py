def estimate_impact(order_size, market_volume):
    return order_size / max(market_volume, 1e-6)
