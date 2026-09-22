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


def _open(url, data=None, headers=None, timeout=15, method=None):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", AGENT)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    return urllib.request.urlopen(req, timeout=timeout)


# ==========================================================================
#  SOURCES -- ask the network something
# ==========================================================================

class Fetch(Part):
    """The text at a URL. Anything that goes wrong gives "" rather than a crash."""
    def __init__(self, url=None, timeout=15, limit=5_000_000):
        self.url, self.timeout, self.limit = url, timeout, limit

    def step(self, ctx):
        try:
            with _open(_pick(self.url, ctx), timeout=self.timeout) as r:
                return r.read(self.limit).decode("utf-8", "ignore")
        except Exception:
            return ""


class Json(Part):
    """Parse the signal as JSON. Bad JSON gives None."""
    def step(self, ctx):
        try:
            return _json.loads(ctx.value)
        except Exception:
            return None


class Status(Part):
    """The HTTP number a URL answers with. 0 means it could not be reached."""
    def __init__(self, url=None, timeout=10): self.url, self.timeout = url, timeout

    def step(self, ctx):
        try:
            with _open(_pick(self.url, ctx), timeout=self.timeout,
                       method="HEAD") as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            return 0


class Reach(Part):
    """True if a TCP connection opens. Works on bare hosts, not just URLs."""
    def __init__(self, host=None, port=443, timeout=5):
        self.host, self.port, self.timeout = host, port, timeout

    def step(self, ctx):
        host = _pick(self.host, ctx)
        if "//" in host:
            host = urllib.parse.urlparse(host).hostname or host
        try:
            socket.create_connection((host, self.port), self.timeout).close()
            return True
        except Exception:
            return False


class Host(Part):
    """Pull the machine name out of a URL."""
    def __init__(self, url=None): self.url = url
    def step(self, ctx):
        return urllib.parse.urlparse(_pick(self.url, ctx)).hostname or ""


class Address(Part):
    """Look a name up in DNS. Unknown names give ""."""
    def __init__(self, host=None): self.host = host
    def step(self, ctx):
        host = _pick(self.host, ctx)
        if "//" in host:
            host = urllib.parse.urlparse(host).hostname or host
        try:    return socket.gethostbyname(host)
        except Exception: return ""


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
