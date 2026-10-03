#!/usr/bin/env python3
"""net -- reaching other machines, as parts.

Same one contract: `step(ctx) -> value`.

Like the file parts, each of these takes its address either as an
argument or from the signal coming down the chain.

    Chain([Const("https://example.com"), Fetch(), Links(), Say()])
    Chain([Fetch("https://example.com"), Links(), Say()])   # same thing

Standard library only -- urllib and socket, nothing to install.
"""

import json as _json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

from .core import Part, _as_list

AGENT = "parts/1.0"


def _pick(arg, ctx):
    return str(arg if arg is not None else ctx.value)


def _bare(url):
    """Just the machine's name, whether you were given one or a whole address."""
    return urllib.parse.urlparse(url).hostname or url if "//" in url else url


def _open(url, data=None, headers=None, timeout=15, method=None):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", AGENT)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    return urllib.request.urlopen(req, timeout=timeout)


# ==========================================================================
#  THE SHAPE, WRITTEN ONCE
# ==========================================================================

class Reaching(Part):
    """A block that asks the network something. Override `about`.

    Nothing here is allowed to raise. Whatever goes wrong -- a dead
    link, no signal, a name that does not exist -- answers `missing`, so
    one bad address never stops a run over a thousand of them.
    """
    missing = ""

    def __init__(self, url=None, timeout=15):
        self.url, self.timeout = url, timeout

    def step(self, ctx):
        try:
            return self.about(_pick(self.url, ctx))
        except Exception:
            return self.missing

    def about(self, url):
        return url


# ==========================================================================
#  SOURCES -- ask the network something
# ==========================================================================

class Fetch(Reaching):
    """The text at a web address. Anything that goes wrong gives ""."""
    def __init__(self, url=None, timeout=15, limit=5_000_000):
        self.url, self.timeout, self.limit = url, timeout, limit
    def about(self, url):
        with _open(url, timeout=self.timeout) as r:
            return r.read(self.limit).decode("utf-8", "ignore")


class Json(Part):
    """Parse the signal as JSON. Bad JSON gives None."""
    def step(self, ctx):
        try:
            return _json.loads(ctx.value)
        except Exception:
            return None


class Status(Reaching):
    """The number a web address answers with. 0 means it was not reached."""
    missing = 0
    def __init__(self, url=None, timeout=10): self.url, self.timeout = url, timeout
    def about(self, url):
        try:
            with _open(url, timeout=self.timeout, method="HEAD") as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code


class Reach(Reaching):
    """Can this machine be reached at all? Works on bare names too."""
    missing = False
    def __init__(self, host=None, port=443, timeout=5):
        self.url, self.port, self.timeout = host, port, timeout
    def about(self, url):
        socket.create_connection((_bare(url), self.port), self.timeout).close()
        return True


class Host(Reaching):
    """Pull the machine's name out of a web address."""
    def about(self, url): return urllib.parse.urlparse(url).hostname or ""


class Address(Reaching):
    """Look a machine's name up and answer its number. Unknown gives ""."""
    def about(self, url): return socket.gethostbyname(_bare(url))


class Links(Part):
    """Every href and src in a page of HTML. Text -> list of URLs.

    Pass the page's own address as `base` to turn relative links absolute.
    """
    RX = re.compile(r'(?:href|src)\s*=\s*["\']([^"\'>\s]+)', re.I)

    def __init__(self, base=None): self.base = base

    def step(self, ctx):
        found = self.RX.findall(str(ctx.value))
        if not self.base:
            return found
        return [urllib.parse.urljoin(self.base, u) for u in found]


class Mine(Part):
    """This machine's own name and address on the network."""
    def step(self, ctx):
        name = socket.gethostname()
        try:    addr = socket.gethostbyname(name)
        except Exception: addr = "127.0.0.1"
        return {"name": name, "address": addr}


# ==========================================================================
#  SINKS -- put something on the network, or pull it to disk
# ==========================================================================

class Send(Part):
    """POST the signal to a URL. Returns what comes back, as text."""
    def __init__(self, url, as_json=True, timeout=20, headers=None):
        self.url, self.as_json = url, as_json
        self.timeout, self.headers = timeout, dict(headers or {})

    def step(self, ctx):
        body = ctx.value
        heads = dict(self.headers)
        if self.as_json:
            data = _json.dumps(body).encode()
            heads.setdefault("Content-Type", "application/json")
        else:
            data = str(body).encode()
        try:
            with _open(self.url, data=data, headers=heads,
                       timeout=self.timeout) as r:
                return r.read(2_000_000).decode("utf-8", "ignore")
        except Exception as e:
            return "error: %s" % e


class Download(Part):
    """Pull whatever URLs come down the chain into a folder.

    Passes the saved paths on, so you can chain straight into Say or Move.
    """
    def __init__(self, into=".", timeout=60):
        self.into, self.timeout = into, timeout

    def step(self, ctx):
        import os
        dest = os.path.abspath(os.path.expanduser(self.into))
        os.makedirs(dest, exist_ok=True)
        saved = []
        for url in _as_list(ctx.value):
            url = str(url)
            name = os.path.basename(urllib.parse.urlparse(url).path) or "download"
            out = os.path.join(dest, name)
            try:
                with _open(url, timeout=self.timeout) as r, open(out, "wb") as fh:
                    while True:
                        chunk = r.read(65536)
                        if not chunk:
                            break
                        fh.write(chunk)
                saved.append(out)
            except Exception:
                pass
        return saved if isinstance(ctx.value, (list, tuple, set)) else \
            (saved[0] if saved else None)


CATALOGUE = {
    "ask":  [Fetch, Status, Reach, Address, Mine],
    "read": [Json, Links, Host],
    "put":  [Send, Download],
}
