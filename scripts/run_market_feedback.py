# scripts/run_market_feedback.py

from market.feedback_loop import run_market_feedback_loop

if __name__ == "__main__":
    market_state = {
        "risk_level": "high",
        "trend": "down",
        "volatility": "extreme",
        "liquidity": "tight"
    }

    result = run_market_feedback_loop(market_state)
    print("=== MARKET FEEDBACK RESULT ===")
    print(result)
