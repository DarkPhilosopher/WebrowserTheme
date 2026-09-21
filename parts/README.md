# parts — the minimal interchangeable kit for a 3D world

Not `when X do Y`. This is the other way to build behaviour: a **signal
flowing down a chain**, the way a wire runs from a sensor, through some
electronics, into a motor.

Python standard library only, one file. Runs anywhere Python runs —
including 32-bit phones where heavier tools won't install.

```bash
python3 parts.py        # runs the demo: a hunter that chases and shoots
```

## The one contract

Every part — sensor, conduit, motor, and any chain of them — is an object
with exactly this:

```python
part.step(ctx) -> float
```

`ctx` carries the world, the body the part is bolted to, and `dt`. A part
reads what it likes and returns a number.

**That is the whole interface**, and it is the reason any part can be
swapped for any other part. A `Chain` is itself a part, so chains nest
inside chains without limit.

## The four kinds

| Kind | Shape | Does |
|---|---|---|
| **Property** | state | Lives on the world or a body — position, mass, fuel |
| **Sensor** | world → number | Ignores its input |
| **Conduit** | number → number | The glue: gain, clamp, delay, PID |
| **Motor** | number → world | Ignores its output |

```python
eye = Chain([Ray(reach=20), Invert(), Bias(20), Gain(0.1), Thrust()])
```

Read that left to right: look ahead → flip it → so *close* is now *big* →
scale it down → push. Four interchangeable parts, one behaviour.

## Properties

Everything the parts read and write.

**On a body** — `pos` `vel` `yaw` `pitch` `spin` `mass` `drag` `radius`
`solid` `alive` `tags` `store` `parts` `force`

**On the world** — `gravity` `bounds` `time` `bodies` `store`

`store` is a plain dict of named numbers, so fuel, hp, ammo and score need
no new machinery.

## Sensors — world in, number out

| Part | Reports |
|---|---|
| `Clock()` | Seconds since the world began |
| `Height()` | How high this body is |
| `Speed()` | How fast it's going, any direction |
| `Heading()` | Which way it faces, in radians |
| `Level(key)` | A named number off the body — fuel, hp, ammo |
| `Near(radius, tag)` | Distance to the nearest other body in range |
| `Touch(tag)` | 1.0 if something is overlapping, else 0.0 |
| `Ray(reach, step, tag)` | Distance to the first thing straight ahead |
| `Bearing(tag, radius)` | Angle from where you look to where the target is |

`Ray` is the rangefinder every robot has. `Bearing` is the steering
sensor — 0 means dead ahead, ±π means directly behind.

## Conduits — number in, number out

| Part | Does |
|---|---|
| `Const(v)` | Ignore the input, emit a fixed number |
| `Gain(k)` | Multiply — the volume knob |
| `Bias(k)` | Add a constant — shifts the zero point |
| `Invert()` | Flip the sign |
| `Clamp(lo, hi)` | Never leave these limits |
| `Threshold(at)` | 1.0 above the line, 0.0 below — analogue becomes digital |
| `Smooth(rate)` | Low-pass filter — kills jitter |
| `Delay(ticks)` | What came in n ticks ago — reaction time |
| `Integrate()` | Accumulate over time — speed becomes distance |
| `Derive()` | Rate of change — distance becomes speed |
| `Osc(period, low, high)` | A wave; needs no input and never sits still |
| `PID(p, i, d)` | Steer the input toward zero |
| `Fan(branches, how)` | Run several chains on one input, combine them |
| `Gate(control)` | Pass the signal only while `control` reads above zero |

`Fan` takes `how="sum" \| "max" \| "min" \| "mul"`. Using `"mul"` with two
`Threshold` branches gives you AND; `"max"` gives you OR.

## Motors — number in, world out

| Part | Does |
|---|---|
| `Thrust(power)` | Push along the way the body faces — the engine |
| `Lift(power)` | Push straight up, whatever it's facing |
| `Turn(rate)` | Set how fast it swings left or right — the rudder |
| `Tilt(rate, limit)` | Point the nose up or down |
| `Store(key)` | Write the signal into a named number |
| `Drain(key, per_second)` | Spend a named number over time — fuel, charge |
| `Spawn(make, ahead, speed, cooldown)` | Emit a new body — the gun |
| `Expire(after)` | Die once the signal has been up for n seconds |
| `Die()` | Remove the body the moment the signal goes up |

### Shooting, and how long a shot lives

The two halves that usually need special-casing are just parts here.

**Fires in the direction the body faces** — `Spawn` reads `body.forward()`
and inherits the shooter's velocity, so a shot from a moving ship leads
correctly:

```python
Chain([Const(1), Spawn(bullet, ahead=1.0, speed=14.0, cooldown=0.4)])
```

**Cleans itself up** — the shot carries its own lifetime, so nothing else
has to track it:

```python
def bullet():
    b = Body("shot", radius=0.2, drag=0.0, tags={"shot"})
    b.parts = [Chain([Const(1), Expire(after=1.5)])]
    return b
```

Swap `Expire(after=1.5)` for `Chain([Near(radius=0.5), Threshold(0.4), Die()])`
and the shot dies on contact instead of on a timer. Same slot, same
interface — that's the interchangeability doing the work.

## A complete creature

From the demo: a hunter that steers toward prey, slows near obstacles, and
fires when the target is roughly ahead and within range.

```python
hunter.parts = [
    # steer: angle to the prey -> PID -> rudder
    Chain([Bearing("prey"), PID(p=2.0, d=0.1), Clamp(-2, 2), Turn()]),

    # throttle: full ahead, but back off when something is close
    Chain([Ray(reach=12.0), Gain(1/12.0), Clamp(0.15, 1.0),
           Gain(4.0), Thrust()]),

    # fire when the prey is roughly ahead AND within 10
    Chain([Fan([Chain([Bearing("prey"), Gain(-1), Clamp(-0.3, 0.3),
                       Threshold(-0.29)]),
                Chain([Near(radius=10.0, tag="prey"), Invert(), Bias(10),
                       Threshold(0.5)])], how="mul"),
           Spawn(bullet, ahead=1.0, speed=14.0, cooldown=0.4)]),
]
```

Three chains, each independent. Delete one and the rest still work.

## Why this shape

- **One signature** means an editor can offer every part in every slot
  without knowing what any of them do.
- **Chains nest**, so a useful combination becomes a single reusable part
  with no new concept.
- **No dependencies and no threads** — it steps when you call `world.step(dt)`,
  so it drops into a terminal loop, a game tick, or a test unchanged.
- **Sensors never write and motors never read**, so a chain can always be
  cut anywhere and inspected.

## Adding your own

Subclass `Part`, override `step`. That's it — it is now usable everywhere
every other part is.

```python
class Bounce(Part):
    """Flip the body's vertical speed when the signal goes up."""
    def step(self, ctx):
        if ctx.value > 0:
            ctx.body.vel.z = abs(ctx.body.vel.z)
        return ctx.value
```

`CATALOGUE` at the bottom of `parts.py` lists every part by kind, ready to
drive a menu or an editor.
