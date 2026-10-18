"""Keyframe tracks and easing."""
import bisect
import math


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def _back(u):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def _elastic(u):
    if u <= 0 or u >= 1:
        return clamp(u)
    return 2 ** (-10 * u) * math.sin((u * 10 - 0.75) * (2 * math.pi / 3)) + 1


EASE = {
    "linear": lambda u: u,
    "in": lambda u: u * u * u,
    "out": lambda u: 1 - (1 - u) ** 3,
    "inout": lambda u: u * u * u * (u * (6 * u - 15) + 10),
    "smooth": lambda u: u * u * (3 - 2 * u),
    "back": _back,
    "elastic": _elastic,
    "step": lambda u: 0.0 if u < 1 else 1.0,
}


def lerp(a, b, u):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * u
    if isinstance(a, tuple) and isinstance(b, tuple):
        return tuple(x + (y - x) * u for x, y in zip(a, b))
    return a if u < 1 else b


class Track:
    """Keys are (time, value, ease); the ease describes how we arrive at that key."""

    def __init__(self, default):
        self.default = default
        self.times = []
        self.keys = []

    def key(self, t, v, ease="inout"):
        i = bisect.bisect_right(self.times, t)
        self.times.insert(i, t)
        self.keys.insert(i, (t, v, ease))
        return self

    def to(self, t0, t1, v, ease="inout"):
        """Hold the current value until t0, then move to v by t1."""
        self.key(t0, self.at(t0), "step" if not isinstance(v, (int, float, tuple)) else "inout")
        self.key(t1, v, ease)
        return self

    def set(self, t, v):
        """Instant change at t."""
        self.key(t - 1e-4, self.at(t - 1e-4), "inout")
        self.key(t, v, "step")
        return self

    def at(self, t):
        if not self.keys:
            return self.default
        if t <= self.times[0]:
            return self.keys[0][1]
        if t >= self.times[-1]:
            return self.keys[-1][1]
        i = bisect.bisect_right(self.times, t)
        t0, v0, _ = self.keys[i - 1]
        t1, v1, ease = self.keys[i]
        u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
        if not isinstance(v0, (int, float, tuple)) or not isinstance(v1, (int, float, tuple)):
            return v0 if u < 1 else v1
        return lerp(v0, v1, EASE[ease](u))
