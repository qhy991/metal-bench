"""Slow integration baseline; not a performance reference. No oracle imports."""
import math


def run(x, weight, rows, columns, epsilon):
    result = []
    for r in range(rows):
        start = r*columns
        inv = 1/math.sqrt(sum(x[start+c]**2 for c in range(columns))/columns+epsilon)
        result.extend(x[start+c]*inv*weight[c] for c in range(columns))
    return result
