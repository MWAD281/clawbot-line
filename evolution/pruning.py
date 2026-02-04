class TraitPruner:
    """
    Remove weak traits over time
    """

    def prune(self, genome, metrics):
        if metrics.current_equity < 0.9:
            for regime in genome:
                genome[regime]["risk_level"] *= 0.9
        return genome
