def adaptive_threshold(noise):
    if noise > 0.7:
        return 0.8
    elif noise < 0.3:
        return 0.5
    return 0.65
