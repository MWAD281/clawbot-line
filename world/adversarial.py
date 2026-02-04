import random


class AdversarialMarket:
    """
    Market that tries to trick policies
    """

    def generate(self, base_market):
        mode = random.choice([
            "fake_breakout",
            "vol_spike",
            "mean_revert_trap",
            "stop_hunt"
        ])

        market = dict(base_market)
        market["adversary_mode"] = mode

        if mode == "fake_breakout":
            market["trend_strength"] *= random.uniform(1.5, 2.0)
            market["reversal_prob"] = 0.7

        elif mode == "vol_spike":
            market["volatility"] *= random.uniform(2.0, 4.0)

        elif mode == "mean_revert_trap":
            market["trend_strength"] *= 0.3

        elif mode == "stop_hunt":
            market["wick_noise"] = random.uniform(1.5, 3.0)

        return market
