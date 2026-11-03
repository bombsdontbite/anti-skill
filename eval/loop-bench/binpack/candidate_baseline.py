def priority(item, bins):
    """Best fit: prefer the bin that would be left with the least room."""
    return [-(b - item) for b in bins]
