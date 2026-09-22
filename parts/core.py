#!/usr/bin/env python3
"""core -- the contract, and the parts that work on any kind of value.

THE ONE CONTRACT
----------------
Every part in this language is an object with exactly this:

    part.step(ctx) -> value

`ctx.value` is the signal travelling down a chain. It may be a number, a
piece of text, a path, a list, or a dict -- whatever the part before it
returned. That is the only rule, and it is why any part can be dropped
into any slot.

THE FOUR KINDS
--------------
    SOURCE    something -> value    ignores its input   (a sensor)
    CONDUIT   value -> value        the glue
    SINK      value -> something    ignores its output  (a motor)
    LINK      holds other parts     Chain, Fan, Each, Keep

A Chain is itself a part, so chains nest without limit.

Standard library only.
"""

import math
import re


# ==========================================================================
#  THE CONTEXT
# ==========================================================================

class Ctx:
    """What every part is handed. world and body are optional -- a file or
    network chain needs neither."""

    def __init__(self, world=None, body=None, dt=0.0, value=None, vars=None):
        self.world = world
        self.body  = body
        self.dt    = dt
        self.value = value
        self.vars  = dict(vars or {})     # named scratch space for a run
        self.time  = getattr(world, "time", 0.0) if world else 0.0


class Part:
    """Everything is one of these. Override step()."""
    def step(self, ctx):
        return ctx.value

    def __repr__(self):
        return "%s()" % type(self).__name__


def run(part, value=None, **vars):
    """Drive one part (usually a Chain) once, outside any world."""
    ctx = Ctx(value=value, vars=vars)
    return part.step(ctx)


# ==========================================================================
#  LINKS -- parts that hold other parts
# ==========================================================================

class Chain(Part):
    """Parts in series. Each one's answer feeds the next."""
    def __init__(self, parts):
        self.parts = list(parts)

    def step(self, ctx):
        for p in self.parts:
            ctx.value = p.step(ctx)
        return ctx.value

    def __repr__(self):
        return "Chain(%d)" % len(self.parts)


class Fan(Part):
    """Run several chains on the same input, then combine.

    how = "sum" | "max" | "min" | "mul" | "all" | "any" | "list" | "first"
    """
    def __init__(self, branches, how="sum"):
        self.branches, self.how = list(branches), how

    def step(self, ctx):
        seed, outs = ctx.value, []
        for b in self.branches:
            ctx.value = seed
            outs.append(b.step(ctx))
        ctx.value = seed
        if not outs:
            return None
        h = self.how
        if h == "list":  return outs
        if h == "first": return outs[0]
        if h == "max":   return max(outs)
        if h == "min":   return min(outs)
        if h == "all":   return all(outs)
        if h == "any":   return any(outs)
        if h == "mul":
            r = 1
            for o in outs: r *= o
            return r
        return sum(outs)


class Each(Part):
    """Apply a part to every item of an incoming list. Returns a new list."""
    def __init__(self, part):
        self.part = part

    def step(self, ctx):
        items = _as_list(ctx.value)
        out = []
        for it in items:
            ctx.value = it
            out.append(self.part.step(ctx))
        ctx.value = out
        return out


class Keep(Part):
    """Keep only the items for which `test` comes back truthy."""
    def __init__(self, test):
        self.test = test

    def step(self, ctx):
        items = _as_list(ctx.value)
        out = []
        for it in items:
            ctx.value = it
            if self.test.step(ctx):
                out.append(it)
        ctx.value = out
        return out


class Drop(Part):
    """The opposite of Keep -- throw away the items that match."""
    def __init__(self, test):
        self.test = test

    def step(self, ctx):
        items = _as_list(ctx.value)
        out = []
        for it in items:
            ctx.value = it
            if not self.test.step(ctx):
                out.append(it)
        ctx.value = out
        return out


class Gate(Part):
    """Pass the signal through only while `control` is truthy, else None."""
    def __init__(self, control):
        self.control = control

    def step(self, ctx):
        keep = ctx.value
        on = self.control.step(ctx)
        ctx.value = keep
        return keep if on else None


class Try(Part):
    """Run a part; if it raises, return `otherwise` instead of crashing."""
    def __init__(self, part, otherwise=None):
        self.part, self.otherwise = part, otherwise

    def step(self, ctx):
        try:
            return self.part.step(ctx)
        except Exception:
            return self.otherwise


def _as_list(v):
    if v is None:                       return []
    if isinstance(v, (list, tuple, set)): return list(v)
    return [v]


# ==========================================================================
#  SOURCES -- ignore the input, produce a value
# ==========================================================================

class Const(Part):
    """A fixed value. Works for numbers, text, paths, lists."""
    def __init__(self, value=1): self.value = value
    def step(self, ctx): return self.value


class Var(Part):
    """Read a named value out of the run's scratch space."""
    def __init__(self, key, default=None): self.key, self.default = key, default
    def step(self, ctx): return ctx.vars.get(self.key, self.default)


class Osc(Part):
    """A wave over time. Needs a world for its clock."""
    def __init__(self, period=2.0, low=-1.0, high=1.0):
        self.period, self.low, self.high = period, low, high
    def step(self, ctx):
        t = getattr(ctx.world, "time", 0.0) if ctx.world else 0.0
        s = math.sin(2 * math.pi * t / self.period)
        return self.low + (s + 1) * 0.5 * (self.high - self.low)


# ==========================================================================
#  NUMBER CONDUITS
# ==========================================================================

class Gain(Part):
    """Multiply."""
    def __init__(self, k=1.0): self.k = k
    def step(self, ctx): return ctx.value * self.k


class Bias(Part):
    """Add a constant."""
    def __init__(self, k=0.0): self.k = k
    def step(self, ctx): return ctx.value + self.k


class Invert(Part):
    """Flip the sign."""
    def step(self, ctx): return -ctx.value


class Minus(Part):
    """Subtract. `other` may be a literal or another part."""
    def __init__(self, other=0.0): self.other = other
    def step(self, ctx): return ctx.value - _val(self.other, ctx)


class Abs(Part):
    """Distance from zero. Turns a difference into a gap."""
    def step(self, ctx): return abs(ctx.value)


class Is(Part):
    """True when the signal equals this. Literal or another part."""
    def __init__(self, other, fold=True): self.other, self.fold = other, fold
    def step(self, ctx):
        a, b = ctx.value, _val(self.other, ctx)
        if self.fold and isinstance(a, str) and isinstance(b, str):
            return a.lower() == b.lower()
        return a == b


class Clamp(Part):
    """Hold it between limits."""
    def __init__(self, lo=0.0, hi=1.0): self.lo, self.hi = lo, hi
    def step(self, ctx): return max(self.lo, min(self.hi, ctx.value))


class Threshold(Part):
    """Above the line or not. Analogue becomes yes/no."""
    def __init__(self, at=0.5, above=1.0, below=0.0):
        self.at, self.above, self.below = at, above, below
    def step(self, ctx): return self.above if ctx.value > self.at else self.below


class Smooth(Part):
    """Low-pass filter. Kills jitter."""
    def __init__(self, rate=0.2): self.rate, self.state = rate, 0.0
    def step(self, ctx):
        self.state += (ctx.value - self.state) * self.rate
        return self.state


class Delay(Part):
    """What came in n steps ago."""
    def __init__(self, steps=1): self.buf = [None] * max(1, steps)
    def step(self, ctx):
        self.buf.append(ctx.value)
        return self.buf.pop(0)


class Integrate(Part):
    """Accumulate over time."""
    def __init__(self, start=0.0, limit=None): self.total, self.limit = start, limit
    def step(self, ctx):
        self.total += ctx.value * (ctx.dt or 1.0)
        if self.limit is not None:
            self.total = max(-self.limit, min(self.limit, self.total))
        return self.total


class Derive(Part):
    """Rate of change."""
    def __init__(self): self.last = None
    def step(self, ctx):
        if self.last is None:
            self.last = ctx.value
            return 0.0
        out = (ctx.value - self.last) / max(ctx.dt or 1.0, 1e-9)
        self.last = ctx.value
        return out


class PID(Part):
    """Steer the input toward zero."""
    def __init__(self, p=1.0, i=0.0, d=0.0):
        self.p, self.i, self.d = p, i, d
        self.total, self.last = 0.0, None
    def step(self, ctx):
        e  = ctx.value
        dt = ctx.dt or 1.0
        self.total += e * dt
        slope = 0.0 if self.last is None else (e - self.last) / max(dt, 1e-9)
        self.last = e
        return self.p * e + self.i * self.total + self.d * slope


# ==========================================================================
#  TEXT CONDUITS
# ==========================================================================

class Lower(Part):
    def step(self, ctx): return str(ctx.value).lower()


class Upper(Part):
    def step(self, ctx): return str(ctx.value).upper()


class Strip(Part):
    def step(self, ctx): return str(ctx.value).strip()


class Split(Part):
    """Text -> list of pieces."""
    def __init__(self, on=None): self.on = on
    def step(self, ctx): return str(ctx.value).split(self.on)


class Join(Part):
    """List -> one piece of text."""
    def __init__(self, with_=", "): self.with_ = with_
    def step(self, ctx):
        return self.with_.join(str(x) for x in _as_list(ctx.value))


class Replace(Part):
    def __init__(self, old, new=""): self.old, self.new = old, new
    def step(self, ctx): return str(ctx.value).replace(self.old, self.new)


class Contains(Part):
    """True when the text is in the value. Case-insensitive by default.

    `text` may be a literal, or another part -- `Contains(Var("name"))`
    tests against whatever was stashed under that name earlier in the run.
    """
    def __init__(self, text, fold=True): self.text, self.fold = text, fold
    def step(self, ctx):
        hay  = str(ctx.value)
        need = str(_val(self.text, ctx))
        if not need:
            return False
        if self.fold:
            hay, need = hay.lower(), need.lower()
        return need in hay


class Match(Part):
    """True when the value matches this regular expression.

    `pattern` may be a literal or another part, same as Contains.
    """
    def __init__(self, pattern, fold=True):
        self.pattern, self.fold = pattern, fold
        self._rx = None if isinstance(pattern, Part) else \
            re.compile(pattern, re.I if fold else 0)

    def step(self, ctx):
        rx = self._rx
        if rx is None:
            rx = re.compile(str(_val(self.pattern, ctx)),
                            re.I if self.fold else 0)
        return bool(rx.search(str(ctx.value)))


class Grab(Part):
    """Pull every regex match out of the value. Text -> list."""
    def __init__(self, pattern, fold=True):
        self.rx = re.compile(pattern, re.I if fold else 0)
    def step(self, ctx): return self.rx.findall(str(ctx.value))


class Text(Part):
    """Render the value into a template. {} is the value itself."""
    def __init__(self, template="{}"): self.template = template
    def step(self, ctx): return self.template.format(ctx.value)


# ==========================================================================
#  LIST CONDUITS
# ==========================================================================

class Count(Part):
    def step(self, ctx): return len(_as_list(ctx.value))


class First(Part):
    def __init__(self, n=1): self.n = n
    def step(self, ctx):
        items = _as_list(ctx.value)
        return items[0] if self.n == 1 else items[:self.n]


class Last(Part):
    def __init__(self, n=1): self.n = n
    def step(self, ctx):
        items = _as_list(ctx.value)
        if not items: return None if self.n == 1 else []
        return items[-1] if self.n == 1 else items[-self.n:]


class Sort(Part):
    def __init__(self, by=None, down=False): self.by, self.down = by, down
    def step(self, ctx):
        items = _as_list(ctx.value)
        if self.by is None:
            return sorted(items, key=str, reverse=self.down)
        return sorted(items, key=lambda x: _field(x, self.by), reverse=self.down)


class Uniq(Part):
    def step(self, ctx):
        seen, out = set(), []
        for x in _as_list(ctx.value):
            k = str(x)
            if k not in seen:
                seen.add(k); out.append(x)
        return out


class Flatten(Part):
    """A list of lists becomes one list."""
    def step(self, ctx):
        out = []
        for x in _as_list(ctx.value):
            out.extend(_as_list(x))
        return out


class Pack(Part):
    """Run several parts on the same input and collect them into a record.

    Fan combines its branches into one answer; Pack keeps them apart under
    names, so later blocks can pick with Field.

        Pack({"name": Name(), "text": Read(), "size": Size()})
    """
    def __init__(self, fields):
        self.fields = dict(fields)

    def step(self, ctx):
        seed, out = ctx.value, {}
        for key, part in self.fields.items():
            ctx.value = seed
            out[key] = part.step(ctx)
        ctx.value = out
        return out


class Field(Part):
    """Pull one named field out of a dict (or attribute off an object)."""
    def __init__(self, key, default=None): self.key, self.default = key, default
    def step(self, ctx): return _field(ctx.value, self.key, self.default)


def _val(x, ctx):
    """Resolve an argument that may be a literal or another part."""
    return x.step(ctx) if isinstance(x, Part) else x


def _field(v, key, default=None):
    if isinstance(v, dict):
        return v.get(key, default)
    return getattr(v, key, default)


# ==========================================================================
#  SINKS -- do something with the value, pass it along unchanged
# ==========================================================================

class Say(Part):
    """Print it. The debugger of this language."""
    def __init__(self, label=None): self.label = label
    def step(self, ctx):
        v = ctx.value
        if isinstance(v, list):
            print("%s%d item%s" % (self.label + ": " if self.label else "",
                                   len(v), "" if len(v) == 1 else "s"))
            for x in v[:200]:
                print("   ", x)
        else:
            print("%s%s" % (self.label + ": " if self.label else "", v))
        return v


class Put(Part):
    """Save a value into the run's scratch space under a name.

    With no value it saves whatever is coming down the chain; with one it
    saves that instead, so `put hot 0.8` sets a variable outright.
    """
    def __init__(self, key, value=None):
        self.key, self.value = key, value

    def step(self, ctx):
        ctx.vars[self.key] = ctx.value if self.value is None else self.value
        return ctx.value


class Tick(Part):
    """Count up in a named variable, a step each time this is reached.

    The way a program makes something move: `tick angle by=10` adds ten
    to `angle` every pass, and anything reading `angle` follows along.
    """
    def __init__(self, key, by=1, start=0, wrap=None):
        self.key, self.by, self.start, self.wrap = key, by, start, wrap

    def step(self, ctx):
        now = ctx.vars.get(self.key, self.start) + self.by
        if self.wrap:
            now %= self.wrap
        ctx.vars[self.key] = now
        return now


class Do(Part):
    """Escape hatch: call your own function with the value."""
    def __init__(self, fn, keep=True): self.fn, self.keep = fn, keep
    def step(self, ctx):
        out = self.fn(ctx.value)
        return ctx.value if self.keep else out


CATALOGUE = {
    "link":    [Chain, Fan, Each, Keep, Drop, Gate, Try],
    "source":  [Const, Var, Osc],
    "number":  [Gain, Bias, Invert, Minus, Abs, Is, Clamp, Threshold, Smooth, Delay,
                Integrate, Derive, PID],
    "text":    [Lower, Upper, Strip, Split, Join, Replace, Contains, Match,
                Grab, Text],
    "list":    [Count, First, Last, Sort, Uniq, Flatten, Field, Pack],
    "sink":    [Say, Put, Tick, Do],
}
