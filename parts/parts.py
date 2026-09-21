#!/usr/bin/env python3
"""parts -- the smallest set of interchangeable pieces for a 3D world.

Not `when X do Y`. This is the other way to build behaviour: a signal
flowing through a chain of parts, the way a wire runs from a sensor
through some electronics into a motor.

THE ONE CONTRACT
----------------
Every part -- sensor, conduit, motor, and any chain of them -- is an
object with exactly this:

    part.step(ctx) -> float

`ctx` carries the world, the body the part is bolted to, and dt. A part
reads what it likes and returns a number. That is the whole interface,
which is why any part can be swapped for any other part.

THE FOUR KINDS
--------------
    PROPERTY   state that lives on the world or a body (position, mass...)
    SENSOR     world -> number      ignores its input
    CONDUIT    number -> number     the glue: gain, clamp, delay, PID...
    MOTOR      number -> world      ignores its output

A Chain is itself a part, so chains nest inside chains without limit.

    eye = Chain([Ray(FWD, 20), Invert(), Bias(20), Gain(0.1), Thrust()])

Python standard library only. Runs anywhere Python runs -- including
32-bit phones.
"""

import math

# ==========================================================================
#  VECTORS -- the only maths type
# ==========================================================================

class V:
    """A 3D vector. Immutable in practice; every operation returns a new one."""
    __slots__ = ("x", "y", "z")

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def __add__(self, o):  return V(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o):  return V(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, k):  return V(self.x * k, self.y * k, self.z * k)
    def __repr__(self):    return "V(%.2f, %.2f, %.2f)" % (self.x, self.y, self.z)

    def length(self):      return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    def dot(self, o):      return self.x * o.x + self.y * o.y + self.z * o.z

    def unit(self):
        n = self.length()
        return V(0, 0, 0) if n < 1e-9 else V(self.x / n, self.y / n, self.z / n)

    def cross(self, o):
        return V(self.y * o.z - self.z * o.y,
                 self.z * o.x - self.x * o.z,
                 self.x * o.y - self.y * o.x)


ZERO = V(0, 0, 0)
UP   = V(0, 0, 1)
FWD  = V(1, 0, 0)          # local forward, before the body's own heading


# ==========================================================================
#  PROPERTIES -- the state the parts read and write
# ==========================================================================

class Body:
    """One thing in the world. These fields ARE the property list."""

    def __init__(self, name="thing", pos=None, **kw):
        # where and how it moves
        self.name     = name
        self.pos      = pos or V()
        self.vel      = V()
        self.yaw      = 0.0          # heading, radians, around Z
        self.pitch    = 0.0          # nose up/down, radians
        self.spin     = 0.0          # yaw change per second
        # what it is made of
        self.mass     = kw.get("mass", 1.0)
        self.drag     = kw.get("drag", 0.1)       # 0 = frictionless
        self.radius   = kw.get("radius", 0.5)
        self.solid    = kw.get("solid", True)
        self.alive    = True
        # anything else you want to hang on it
        self.tags     = set(kw.get("tags", ()))
        self.store    = dict(kw.get("store", {}))  # named numbers: fuel, hp...
        self.parts    = list(kw.get("parts", []))
        self.force    = V()          # accumulated by motors, spent each tick

    def forward(self):
        """Unit vector the body is facing, from yaw + pitch."""
        cp = math.cos(self.pitch)
        return V(math.cos(self.yaw) * cp, math.sin(self.yaw) * cp,
                 math.sin(self.pitch))

    def right(self):
        return V(math.sin(self.yaw), -math.cos(self.yaw), 0.0)


class World:
    """Everything that exists, plus the rules that apply to all of it."""

    def __init__(self, gravity=V(0, 0, -9.81), bounds=None):
        self.bodies  = []
        self.gravity = gravity
        self.bounds  = bounds        # (V(min), V(max)) or None for open space
        self.time    = 0.0
        self.store   = {}            # world-wide named numbers: score, wind...

    def add(self, body):
        self.bodies.append(body)
        return body

    def near(self, pos, radius, skip=None):
        """Every living body whose centre is within radius."""
        out = []
        for b in self.bodies:
            if b is skip or not b.alive:
                continue
            if (b.pos - pos).length() <= radius:
                out.append(b)
        return out

    def step(self, dt=1 / 30.0):
        """Run every part on every body, then move everything."""
        for b in list(self.bodies):
            if not b.alive:
                continue
            ctx = Ctx(self, b, dt)
            for p in b.parts:
                p.step(ctx)

        for b in list(self.bodies):
            if not b.alive:
                continue
            acc = self.gravity + (b.force * (1.0 / max(b.mass, 1e-6)))
            b.vel = b.vel + acc * dt
            b.vel = b.vel * max(0.0, 1.0 - b.drag * dt)
            b.pos = b.pos + b.vel * dt
            b.yaw += b.spin * dt
            b.force = V()
            if self.bounds:
                self._clip(b)

        self.bodies = [b for b in self.bodies if b.alive]
        self.time += dt

    def _clip(self, b):
        lo, hi = self.bounds
        for ax in ("x", "y", "z"):
            v = getattr(b.pos, ax)
            if v < getattr(lo, ax):
                setattr(b.pos, ax, getattr(lo, ax)); setattr(b.vel, ax, 0.0)
            elif v > getattr(hi, ax):
                setattr(b.pos, ax, getattr(hi, ax)); setattr(b.vel, ax, 0.0)


class Ctx:
    """What a part is handed on every tick."""
    __slots__ = ("world", "body", "dt", "value")

    def __init__(self, world, body, dt):
        self.world, self.body, self.dt = world, body, dt
        self.value = 0.0             # the signal travelling down a chain


# ==========================================================================
#  THE BASE PART
# ==========================================================================

class Part:
    """Everything below is one of these. Override step()."""
    def step(self, ctx):
        return ctx.value


class Chain(Part):
    """Parts in series. The value from each is fed to the next.

    A Chain is a Part, so a chain can sit inside another chain.
    """
    def __init__(self, parts):
        self.parts = list(parts)

    def step(self, ctx):
        for p in self.parts:
            ctx.value = p.step(ctx)
        return ctx.value


# ==========================================================================
#  SENSORS -- world in, number out
# ==========================================================================

class Clock(Part):
    """Seconds since the world began."""
    def step(self, ctx): return ctx.world.time


class Height(Part):
    """How high this body is."""
    def step(self, ctx): return ctx.body.pos.z


class Speed(Part):
    """How fast it is going, in any direction."""
    def step(self, ctx): return ctx.body.vel.length()


class Heading(Part):
    """Which way it faces, in radians."""
    def step(self, ctx): return ctx.body.yaw


class Level(Part):
    """Read a named number off the body (fuel, hp, ammo...)."""
    def __init__(self, key, default=0.0):
        self.key, self.default = key, default

    def step(self, ctx): return ctx.body.store.get(self.key, self.default)


class Near(Part):
    """Distance to the nearest other body within range, else `miss`."""
    def __init__(self, radius=10.0, tag=None, miss=None):
        self.radius, self.tag = radius, tag
        self.miss = radius if miss is None else miss

    def step(self, ctx):
        best = self.miss
        for b in ctx.world.near(ctx.body.pos, self.radius, skip=ctx.body):
            if self.tag and self.tag not in b.tags:
                continue
            d = (b.pos - ctx.body.pos).length()
            if d < best:
                best = d
        return best


class Touch(Part):
    """1.0 if something is overlapping this body, else 0.0."""
    def __init__(self, tag=None):
        self.tag = tag

    def step(self, ctx):
        me = ctx.body
        for b in ctx.world.near(me.pos, me.radius + 2.0, skip=me):
            if self.tag and self.tag not in b.tags:
                continue
            if (b.pos - me.pos).length() <= me.radius + b.radius:
                return 1.0
        return 0.0


class Ray(Part):
    """March forward and report the distance to the first thing hit.

    The sensor every robot has: a rangefinder pointed where you look.
    Returns `reach` when nothing is in the way.
    """
    def __init__(self, reach=20.0, step=0.5, tag=None):
        self.reach, self.stride, self.tag = reach, step, tag

    def step(self, ctx):
        me  = ctx.body
        dir = me.forward()
        d   = self.stride
        while d <= self.reach:
            at = me.pos + dir * d
            for b in ctx.world.near(at, 0.0001 + self.stride, skip=me):
                if not b.solid:
                    continue
                if self.tag and self.tag not in b.tags:
                    continue
                if (b.pos - at).length() <= b.radius:
                    return d
            d += self.stride
        return self.reach


class Bearing(Part):
    """Angle between where the body looks and where the target is.

    0 means dead ahead; +/-pi means directly behind. The steering sensor.
    """
    def __init__(self, tag, radius=50.0):
        self.tag, self.radius = tag, radius

    def step(self, ctx):
        me   = ctx.body
        best, bd = None, self.radius
        for b in ctx.world.near(me.pos, self.radius, skip=me):
            if self.tag not in b.tags:
                continue
            d = (b.pos - me.pos).length()
            if d < bd:
                best, bd = b, d
        if best is None:
            return 0.0
        to = best.pos - me.pos
        want = math.atan2(to.y, to.x)
        return math.atan2(math.sin(want - me.yaw), math.cos(want - me.yaw))


# ==========================================================================
#  CONDUITS -- number in, number out. The interchangeable middle.
# ==========================================================================

class Const(Part):
    """Ignore the input, emit a fixed number."""
    def __init__(self, value=1.0): self.value = float(value)
    def step(self, ctx): return self.value


class Gain(Part):
    """Multiply. The volume knob."""
    def __init__(self, k=1.0): self.k = float(k)
    def step(self, ctx): return ctx.value * self.k


class Bias(Part):
    """Add a constant. Shifts the zero point."""
    def __init__(self, k=0.0): self.k = float(k)
    def step(self, ctx): return ctx.value + self.k


class Invert(Part):
    """Flip the sign."""
    def step(self, ctx): return -ctx.value


class Clamp(Part):
    """Never let it leave these limits."""
    def __init__(self, lo=0.0, hi=1.0): self.lo, self.hi = lo, hi
    def step(self, ctx): return max(self.lo, min(self.hi, ctx.value))


class Threshold(Part):
    """Comparator: 1.0 above the line, 0.0 below. Analogue becomes digital."""
    def __init__(self, at=0.5, above=1.0, below=0.0):
        self.at, self.above, self.below = at, above, below
    def step(self, ctx): return self.above if ctx.value > self.at else self.below


class Smooth(Part):
    """Low-pass filter. Lets change through slowly, kills jitter."""
    def __init__(self, rate=0.2):
        self.rate, self.state = rate, 0.0
    def step(self, ctx):
        self.state += (ctx.value - self.state) * self.rate
        return self.state


class Delay(Part):
    """Return what came in n ticks ago. Reaction time."""
    def __init__(self, ticks=1):
        self.buf = [0.0] * max(1, ticks)
    def step(self, ctx):
        self.buf.append(ctx.value)
        return self.buf.pop(0)


class Integrate(Part):
    """Accumulate over time. Speed becomes distance."""
    def __init__(self, start=0.0, limit=None):
        self.total, self.limit = start, limit
    def step(self, ctx):
        self.total += ctx.value * ctx.dt
        if self.limit is not None:
            self.total = max(-self.limit, min(self.limit, self.total))
        return self.total


class Derive(Part):
    """Rate of change. Distance becomes speed."""
    def __init__(self):
        self.last = None
    def step(self, ctx):
        if self.last is None:
            self.last = ctx.value
            return 0.0
        out, self.last = (ctx.value - self.last) / max(ctx.dt, 1e-9), ctx.value
        return out


class Osc(Part):
    """A wave. The only part that needs no input and never sits still."""
    def __init__(self, period=2.0, low=-1.0, high=1.0):
        self.period, self.low, self.high = period, low, high
    def step(self, ctx):
        t = math.sin(2 * math.pi * ctx.world.time / self.period)
        return self.low + (t + 1) * 0.5 * (self.high - self.low)


class PID(Part):
    """Steer the input toward zero. The whole of control theory, in one part."""
    def __init__(self, p=1.0, i=0.0, d=0.0):
        self.p, self.i, self.d = p, i, d
        self.total, self.last = 0.0, None
    def step(self, ctx):
        e = ctx.value
        self.total += e * ctx.dt
        slope = 0.0 if self.last is None else (e - self.last) / max(ctx.dt, 1e-9)
        self.last = e
        return self.p * e + self.i * self.total + self.d * slope


class Fan(Part):
    """Run several chains on the same input and combine their answers.

    how = "sum" | "max" | "min" | "mul"
    """
    def __init__(self, branches, how="sum"):
        self.branches, self.how = list(branches), how
    def step(self, ctx):
        seed, outs = ctx.value, []
        for b in self.branches:
            ctx.value = seed
            outs.append(b.step(ctx))
        if not outs:
            return 0.0
        if self.how == "max": return max(outs)
        if self.how == "min": return min(outs)
        if self.how == "mul":
            r = 1.0
            for o in outs: r *= o
            return r
        return sum(outs)


class Gate(Part):
    """Let the signal through only while `control` reads above zero."""
    def __init__(self, control):
        self.control = control
    def step(self, ctx):
        keep = ctx.value
        on = self.control.step(ctx)
        ctx.value = keep
        return keep if on > 0 else 0.0


# ==========================================================================
#  MOTORS -- number in, world out
# ==========================================================================

class Thrust(Part):
    """Push along the way the body faces. The engine."""
    def __init__(self, power=1.0): self.power = power
    def step(self, ctx):
        ctx.body.force = ctx.body.force + ctx.body.forward() * (ctx.value * self.power)
        return ctx.value


class Lift(Part):
    """Push straight up, whatever the body is facing."""
    def __init__(self, power=1.0): self.power = power
    def step(self, ctx):
        ctx.body.force = ctx.body.force + UP * (ctx.value * self.power)
        return ctx.value


class Turn(Part):
    """Set how fast it swings left or right. The rudder."""
    def __init__(self, rate=1.0): self.rate = rate
    def step(self, ctx):
        ctx.body.spin = ctx.value * self.rate
        return ctx.value


class Tilt(Part):
    """Point the nose up or down."""
    def __init__(self, rate=1.0, limit=1.4): self.rate, self.limit = rate, limit
    def step(self, ctx):
        b = ctx.body
        b.pitch = max(-self.limit,
                      min(self.limit, b.pitch + ctx.value * self.rate * ctx.dt))
        return ctx.value


class Store(Part):
    """Write the signal into a named number on the body."""
    def __init__(self, key): self.key = key
    def step(self, ctx):
        ctx.body.store[self.key] = ctx.value
        return ctx.value


class Drain(Part):
    """Spend a named number over time. Fuel, charge, health."""
    def __init__(self, key, per_second=1.0):
        self.key, self.rate = key, per_second
    def step(self, ctx):
        s = ctx.body.store
        s[self.key] = s.get(self.key, 0.0) - abs(ctx.value) * self.rate * ctx.dt
        return s[self.key]


class Spawn(Part):
    """Emit a new body when the signal crosses zero going up. The gun."""
    def __init__(self, make, ahead=1.0, speed=10.0, cooldown=0.25):
        self.make, self.ahead, self.speed = make, ahead, speed
        self.cooldown, self.ready = cooldown, 0.0
    def step(self, ctx):
        if ctx.value > 0 and ctx.world.time >= self.ready:
            me  = ctx.body
            dir = me.forward()
            shot = self.make()
            shot.pos = me.pos + dir * self.ahead
            shot.vel = me.vel + dir * self.speed
            shot.yaw = me.yaw
            ctx.world.add(shot)
            self.ready = ctx.world.time + self.cooldown
        return ctx.value


class Expire(Part):
    """Die once the signal has been above zero for `after` seconds.

    Wire it to Const(1) and every shot cleans itself up.
    """
    def __init__(self, after=2.0):
        self.after, self.age = after, 0.0
    def step(self, ctx):
        if ctx.value > 0:
            self.age += ctx.dt
            if self.age >= self.after:
                ctx.body.alive = False
        return ctx.value


class Die(Part):
    """Remove the body the moment the signal goes above zero."""
    def step(self, ctx):
        if ctx.value > 0:
            ctx.body.alive = False
        return ctx.value


# ==========================================================================
#  THE WHOLE CATALOGUE, for menus and editors
# ==========================================================================

CATALOGUE = {
    "sensor":  [Clock, Height, Speed, Heading, Level, Near, Touch, Ray, Bearing],
    "conduit": [Const, Gain, Bias, Invert, Clamp, Threshold, Smooth, Delay,
                Integrate, Derive, Osc, PID, Fan, Gate],
    "motor":   [Thrust, Lift, Turn, Tilt, Store, Drain, Spawn, Expire, Die],
    "link":    [Chain],
}


# ==========================================================================
#  DEMO -- a hunter that chases, a shot that expires
# ==========================================================================

def _demo():
    world = World(gravity=ZERO)

    def bullet():
        b = Body("shot", radius=0.2, drag=0.0, tags={"shot"})
        # a shot needs nothing but a clock running down
        b.parts = [Chain([Const(1), Expire(after=1.5)])]
        return b

    prey = world.add(Body("prey", pos=V(14, 6, 0), drag=0.4, tags={"prey"}))
    prey.parts = [Chain([Osc(period=4.0), Gain(0.8), Turn()]),
                  Chain([Const(1.0), Thrust(power=3.0)])]

    hunter = world.add(Body("hunter", pos=V(0, 0, 0), drag=0.4, tags={"hunter"}))
    hunter.parts = [
        # steer: angle to the prey -> PID -> rudder
        Chain([Bearing("prey"), PID(p=2.0, d=0.1), Clamp(-2, 2), Turn()]),
        # throttle: full ahead, but back off when something is very close
        Chain([Ray(reach=12.0), Gain(1 / 12.0), Clamp(0.15, 1.0),
               Gain(4.0), Thrust()]),
        # fire whenever the prey is roughly ahead and within 10
        Chain([Fan([Chain([Bearing("prey"), Gain(-1), Clamp(-0.3, 0.3),
                           Threshold(-0.29)]),
                    Chain([Near(radius=10.0, tag="prey"), Invert(), Bias(10),
                           Threshold(0.5)])], how="mul"),
               Spawn(bullet, ahead=1.0, speed=14.0, cooldown=0.4)]),
    ]

    print("tick   hunter                 dist   shots")
    for i in range(90):
        world.step(1 / 30.0)
        if i % 10 == 0:
            d = (prey.pos - hunter.pos).length()
            shots = sum(1 for b in world.bodies if "shot" in b.tags)
            print("%4d   %-22s %5.1f   %d" % (i, hunter.pos, d, shots))
    print("\nbodies left:", len(world.bodies),
          "(shots expire after 1.5s on their own)")


if __name__ == "__main__":
    _demo()
