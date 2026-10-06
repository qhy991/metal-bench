"""Mathematical oracle and deterministic test inputs, independent of candidates."""
import math
import random
import struct


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def inputs(rows, columns, distribution, seed):
    rng = random.Random(seed)
    scales = {'uniform': 1.0, 'near_zero': 1e-5}
    if distribution in scales:
        x = [f32(rng.uniform(-scales[distribution], scales[distribution])) for _ in range(rows*columns)]
    elif distribution == 'zeros':
        x = [0.0] * (rows*columns)
    elif distribution == 'alternating':
        x = [f32((-1 if i % 2 else 1) * rng.uniform(0.5, 2)) for i in range(rows*columns)]
    elif distribution == 'mixed_magnitude':
        x = [f32(rng.uniform(-1, 1) * (100 if i % 3 == 0 else 1e-3)) for i in range(rows*columns)]
    else:
        raise ValueError('unknown distribution')
    weight = [f32(rng.uniform(-1.5, 1.5)) for _ in range(columns)]
    return x, weight


def reference(x, weight, rows, columns, epsilon):
    out = []
    for row in range(rows):
        values = x[row*columns:(row+1)*columns]
        inv = 1/math.sqrt(math.fsum(v*v for v in values)/columns + epsilon)
        out.extend(f32(v*inv*w) for v, w in zip(values, weight))
    return out


def compare(expected, actual, *, atol, rtol):
    if not isinstance(actual, list) or len(actual) != len(expected):
        raise ValueError('output shape/length differs')
    maximum = 0.0
    for i, (want, got) in enumerate(zip(expected, actual)):
        if type(got) not in (int, float) or not math.isfinite(got):
            raise ValueError(f'nonfinite/non-numeric output at {i}')
        got = f32(got)
        delta = abs(got-want)
        maximum = max(maximum, delta)
        if delta > atol + rtol*abs(want):
            raise ValueError(f'output mismatch at {i}: abs_error={delta}')
    return maximum


def mean30(samples):
    if not isinstance(samples, list) or len(samples) != 30:
        raise ValueError('timing requires exactly 30 samples')
    if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in samples):
        raise ValueError('GPU intervals must be finite and positive')
    return math.fsum(samples)/30/64
