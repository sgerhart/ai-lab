def covariance(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) == 0: return 0.0
    mx, my = sum(x)/len(x), sum(y)/len(y)
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x))) / len(x)
