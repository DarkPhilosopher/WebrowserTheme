#!/usr/bin/env python3
"""space -- a 3D world, its bodies, and the parts that sense and move them.

Same one contract: `step(ctx) -> value`.

The number conduits these chains need -- Gain, Clamp, PID and the rest --
live in core, because they are not about space at all. That is the point
of splitting the language up: a PID does not care whether it is steering
a ship or throttling a file copy.

Standard library only.
"""

import math

from .core import Part, Ctx


# ==========================================================================
#  VECTORS
# ==========================================================================

class V:
    """A 3D vector. Every operation returns a new one."""
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
        return V() if n < 1e-9 else V(self.x / n, self.y / n, self.z / n)

    def cross(self, o):
        return V(self.y * o.z - self.z * o.y,
                 self.z * o.x - self.x * o.z,
                 self.x * o.y - self.y * o.x)


ZERO = V(0, 0, 0)
UP   = V(0, 0, 1)
FWD  = V(1, 0, 0)


# ==========================================================================
#  PROPERTIES -- the state parts read and write
# ==========================================================================

class Body:
    """One thing in the world. These fields ARE the property list."""

    def __init__(self, name="thing", pos=None, **kw):
        self.name   = name
        self.pos    = pos or V()
        self.vel    = V()
        self.yaw    = 0.0
        self.pitch  = 0.0
        self.spin   = 0.0
        self.mass   = kw.get("mass", 1.0)
        self.drag   = kw.get("drag", 0.1)
        self.radius = kw.get("radius", 0.5)
        self.solid  = kw.get("solid", True)
        self.alive  = True
        self.tags   = set(kw.get("tags", ()))
        self.store  = dict(kw.get("store", {}))
        self.parts  = list(kw.get("parts", []))
        self.force  = V()

    def forward(self):
        cp = math.cos(self.pitch)
        return V(math.cos(self.yaw) * cp, math.sin(self.yaw) * cp,
                 math.sin(self.pitch))

    def right(self):
        return V(math.sin(self.yaw), -math.cos(self.yaw), 0.0)


class World:
    """Everything that exists, plus the rules that apply to all of it."""

    def __init__(self, gravity=None, bounds=None):
        self.bodies  = []
        self.gravity = V(0, 0, -9.81) if gravity is None else gravity
        self.bounds  = bounds
        self.time    = 0.0
        self.store   = {}

    def add(self, body):
        self.bodies.append(body)
        return body

    def near(self, pos, radius, skip=None):
        out = []
        for b in self.bodies:
            if b is skip or not b.alive:
                continue
            if (b.pos - pos).length() <= radius:
                out.append(b)
        return out

    def step(self, dt=1 / 30.0):
        for b in list(self.bodies):
            if not b.alive:
                continue
            ctx = Ctx(world=self, body=b, dt=dt, value=0.0)
            for p in b.parts:
                ctx.value = 0.0
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


# ==========================================================================
#  SENSORS -- world in, number out
# ==========================================================================

class Clock(Part):
    """Seconds since the world began."""
    def step(self, ctx): return ctx.world.time


class Height(Part):
    """How high above the ground this body is."""
    def step(self, ctx): return ctx.body.pos.z


class Speed(Part):
    """How fast it is going, whichever way it is going."""
    def step(self, ctx): return ctx.body.vel.length()


class Heading(Part):
    """Which way it is facing, as an angle."""
    def step(self, ctx): return ctx.body.yaw


class Level(Part):
    """Read a named number off the body -- fuel, hp, ammo."""
    def __init__(self, key, default=0.0): self.key, self.default = key, default
    def step(self, ctx): return ctx.body.store.get(self.key, self.default)


class Near(Part):
    """Distance to the nearest other body in range, else `miss`."""
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
    """1.0 if something is overlapping this body."""
    def __init__(self, tag=None): self.tag = tag

    def step(self, ctx):
        me = ctx.body
        for b in ctx.world.near(me.pos, me.radius + 2.0, skip=me):
            if self.tag and self.tag not in b.tags:
                continue
            if (b.pos - me.pos).length() <= me.radius + b.radius:
                return 1.0
        return 0.0


class Ray(Part):
    """Distance to the first solid thing straight ahead. The rangefinder."""
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
    """Angle from where you look to where the target is. 0 is dead ahead."""
    def __init__(self, tag, radius=50.0): self.tag, self.radius = tag, radius

    def step(self, ctx):
        me = ctx.body
        best, bd = None, self.radius
        for b in ctx.world.near(me.pos, self.radius, skip=me):
            if self.tag not in b.tags:
                continue
            d = (b.pos - me.pos).length()
            if d < bd:
                best, bd = b, d
        if best is None:
            return 0.0
        to   = best.pos - me.pos
        want = math.atan2(to.y, to.x)
        return math.atan2(math.sin(want - me.yaw), math.cos(want - me.yaw))


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
    """Push it straight up, whatever way it is facing."""
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
    """Point its nose up or down."""
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
    def __init__(self, key, per_second=1.0): self.key, self.rate = key, per_second
    def step(self, ctx):
        s = ctx.body.store
        s[self.key] = s.get(self.key, 0.0) - abs(ctx.value) * self.rate * ctx.dt
        return s[self.key]


class Spawn(Part):
    """Emit a new body while the signal is up. The gun.

    Fires along body.forward() and inherits the shooter's velocity, so a
    shot from something moving leads correctly without extra work.
    """
    def __init__(self, make, ahead=1.0, speed=10.0, cooldown=0.25):
        self.make, self.ahead, self.speed = make, ahead, speed
        self.cooldown, self.ready = cooldown, 0.0

    def step(self, ctx):
        if ctx.value and ctx.value > 0 and ctx.world.time >= self.ready:
            me   = ctx.body
            dir  = me.forward()
            shot = self.make()
            shot.pos = me.pos + dir * self.ahead
            shot.vel = me.vel + dir * self.speed
            shot.yaw = me.yaw
            ctx.world.add(shot)
            self.ready = ctx.world.time + self.cooldown
        return ctx.value


class Expire(Part):
    """Die once the signal has been up for `after` seconds."""
    def __init__(self, after=2.0): self.after, self.age = after, 0.0
    def step(self, ctx):
        if ctx.value and ctx.value > 0:
            self.age += ctx.dt
            if self.age >= self.after:
                ctx.body.alive = False
        return ctx.value


class Die(Part):
    """Remove the body the moment the signal goes up."""
    def step(self, ctx):
        if ctx.value and ctx.value > 0:
            ctx.body.alive = False
        return ctx.value


CATALOGUE = {
    "sensor": [Clock, Height, Speed, Heading, Level, Near, Touch, Ray, Bearing],
    "motor":  [Thrust, Lift, Turn, Tilt, Store, Drain, Spawn, Expire, Die],
}
