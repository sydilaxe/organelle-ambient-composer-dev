"""Write Pure Data patches from Python.

Canvas: objects, messages, comments, subpatches and connections, with automatic layout.
Steps (proc / X / Send / Call / If / Loop ...): a tiny imperative language that compiles to
[t b b ...] chains of [expr] boxes reading and writing global [value]s and arrays. All of the
composer's control logic is written with it, so every Pd box stays vanilla (Pd 0.53).
"""


def esc(text):
    out = text.replace("$", "\\$")
    out = out.replace(",", " \\,").replace(";", " \\;")
    return out


class Canvas:
    def __init__(self, name=None, w=1400, h=900, font=10):
        self.name, self.w, self.h, self.font = name, w, h, font
        self.items, self.conns = [], []
        self.cx, self.cy = 20, 20

    # ---- layout: objects flow down a column; col() starts a new one
    def col(self, dx=230):
        self.cx += dx
        self.cy = 20

    def _place(self, x, y):
        if x is None:
            x, y = self.cx, self.cy
            self.cy += 24
            if self.cy > 3600:
                self.col()
        return x, y

    def obj(self, text, x=None, y=None):
        x, y = self._place(x, y)
        self.items.append(("obj", (x, y, text)))
        return len(self.items) - 1

    def msg(self, text, x=None, y=None):
        x, y = self._place(x, y)
        self.items.append(("msg", (x, y, text)))
        return len(self.items) - 1

    def comment(self, text, x=None, y=None):
        x, y = self._place(x, y)
        self.items.append(("text", (x, y, text)))
        return len(self.items) - 1

    def sub(self, canvas, x=None, y=None):
        x, y = self._place(x, y)
        self.items.append(("sub", (x, y, canvas)))
        return len(self.items) - 1

    # ---- wiring
    def c(self, a, ao, b, bi=0):
        if isinstance(a, tuple):
            a, ao = a
        self.conns.append((a, ao, b, bi))

    def to(self, src, text, ao=0, bi=0):
        n = self.obj(text)
        if src is not None:
            self.c(src, ao, n, bi)
        return n

    def m(self, src, text, ao=0):
        n = self.msg(text)
        if src is not None:
            self.c(src, ao, n, 0)
        return n

    def ch(self, src, *texts, ao=0):
        prev = src
        for i, t in enumerate(texts):
            n = self.obj(t)
            if prev is not None:
                self.c(prev, ao if i == 0 else 0, n, 0)
            prev = n
        return prev

    def recv(self, name):
        return self.obj("r " + name)

    # ---- output
    def render(self, top=True, rx=0, ry=0):
        lines = []
        if top:
            lines.append(f"#N canvas 50 50 {self.w} {self.h} {self.font};")
        else:
            lines.append(f"#N canvas 50 50 {self.w} {self.h} {self.name} 0;")
        for kind, p in self.items:
            if kind == "sub":
                x, y, cv = p
                lines.extend(cv.render(top=False, rx=x, ry=y))
            else:
                x, y, t = p
                tag = {"obj": "obj", "msg": "msg", "text": "text"}[kind]
                lines.append(f"#X {tag} {x} {y} {esc(t)};")
        for a, ao, b, bi in self.conns:
            lines.append(f"#X connect {a} {ao} {b} {bi};")
        if not top:
            lines.append(f"#X restore {rx} {ry} pd {self.name};")
        return lines

    def save(self, path):
        with open(path, "w") as f:
            f.write("\n".join(self.render()) + "\n")


# ======================================================================================
# Steps. A step is a function (canvas, src) -> None, where src is (object, outlet) giving a bang.
# ======================================================================================

def _sink(c, src, sink):
    """Connect src to a sink: 'v name' / 's name' / any object text / (obj, inlet) / callable."""
    if sink is None:
        return
    if callable(sink):
        sink(c, src)
    elif isinstance(sink, tuple):
        c.c(src[0], src[1], sink[0], sink[1])
    else:
        c.c(src[0], src[1], c.obj(sink), 0)


def run_steps(c, src, steps):
    steps = [s for s in steps if s is not None]
    if not steps:
        return
    if len(steps) == 1:
        steps[0](c, src)
        return
    t = c.obj("t " + " ".join(["b"] * len(steps)))
    c.c(*(src if isinstance(src, tuple) else (src, 0)), t, 0)
    for i, st in enumerate(steps):
        st(c, (t, len(steps) - 1 - i))


def proc(c, recv, steps):
    """[r recv] -> steps in order. Returns the receive object."""
    r = c.recv(recv)
    run_steps(c, (r, 0), steps)
    c.col()
    return r


def X(expr, *sinks):
    """Evaluate [expr e0; e1; ...] and send outlet i to sinks[i] (outlets fire right to left)."""
    def st(c, src):
        e = c.obj("expr " + expr)
        c.c(*src, e, 0)
        for i, s in enumerate(sinks):
            _sink(c, (e, i), s)
    return st


def V(name, expr):
    return X(expr, "v " + name)


def T(table, idx, val):
    """table[idx] = val"""
    def st(c, src):
        e = c.obj(f"expr {val}; {idx}")
        c.c(*src, e, 0)
        tw = c.obj("tabwrite " + table)
        c.c(e, 1, tw, 1)
        c.c(e, 0, tw, 0)
    return st


def Send(name, text=None):
    """bang [s name], or send a fixed message."""
    def st(c, src):
        if text is None:
            s = c.obj("s " + name)
            c.c(*src, s, 0)
        else:
            m = c.msg(text)
            c.c(*src, m, 0)
            c.c(m, 0, c.obj("s " + name), 0)
    return st


Call = Send


def SendL(name, exprs, fmt=None):
    """Evaluate several exprs and send them as one list (optionally through a message format)."""
    def st(c, src):
        e = c.obj("expr " + "; ".join(exprs))
        c.c(*src, e, 0)
        if len(exprs) == 1:
            out = e
        else:
            out = c.obj("pack " + " ".join(["f"] * len(exprs)))
            for i in range(len(exprs)):
                c.c(e, i, out, i)
        if fmt:
            m = c.msg(fmt)
            c.c(out, 0, m, 0)
            out = m
        c.c(out, 0, c.obj("s " + name), 0)
    return st


def If(cond, steps, else_steps=None):
    def st(c, src):
        e = c.obj("expr " + cond)
        c.c(*src, e, 0)
        s = c.obj("sel 0")
        c.c(e, 0, s, 0)
        if steps:
            b = c.obj("b")
            c.c(s, 1, b, 0)
            run_steps(c, (b, 0), steps)
        if else_steps:
            run_steps(c, (s, 0), else_steps)
    return st


def Loop(count, var, steps):
    """for var in 0..count-1: steps"""
    def st(c, src):
        e = c.obj("expr " + count)
        c.c(*src, e, 0)
        tf = c.obj("t f b")
        c.c(e, 0, tf, 0)
        f = c.obj("f")
        z = c.msg("0")
        c.c(tf, 1, z, 0)
        c.c(z, 0, f, 1)
        u = c.obj("until")
        c.c(tf, 0, u, 0)
        c.c(u, 0, f, 0)
        p = c.obj("+ 1")
        c.c(f, 0, p, 0)
        c.c(p, 0, f, 1)
        tb = c.obj("t b f")
        c.c(f, 0, tb, 0)
        c.c(tb, 1, c.obj("v " + var), 0)
        run_steps(c, (tb, 0), steps)
    return st


def Raw(fn):
    return fn


def lookup(c, src, names, dest, prefix="symbol "):
    """float index at src -> [sel 0 1 ..] -> 'symbol name' messages into dest (obj, inlet)."""
    s = c.obj("sel " + " ".join(str(i) for i in range(len(names))))
    c.c(*(src if isinstance(src, tuple) else (src, 0)), s, 0)
    for i, n in enumerate(names):
        m = c.msg(prefix + n.replace(" ", "\\ "))       # an escaped space keeps 'stereo wide' one symbol
        c.c(s, i, m, 0)
        c.c(m, 0, dest[0], dest[1])
    return s


def Line(recv, fmt, parts, dest):
    """Screen/text line: on [r recv] evaluate parts and send fmt (a message using $1..$n) to dest.
    parts: ('f', expr) or ('s', expr, [names])."""
    def build(c):
        r = c.recv(recv)
        n = len(parts)
        pk = c.obj("pack " + " ".join("s" if p[0] == "s" else "f" for p in parts))
        t = c.obj("t " + " ".join(["b"] * n))
        c.c(r, 0, t, 0)
        for i, p in enumerate(parts):
            e = c.obj("expr " + p[1])
            c.c(t, i, e, 0)
            if p[0] == "f":
                c.c(e, 0, pk, i)
            else:
                lookup(c, (e, 0), p[2], (pk, i))
        m = c.msg(fmt)
        c.c(pk, 0, m, 0)
        c.c(m, 0, c.obj("s " + dest), 0)
        c.col()
    return build


def Arm(tick, expr, stop=None):
    """(re)start a [delay] of expr ms that then bangs [s tick]; [s stop] cancels it."""
    def st(c, src):
        e = c.obj("expr " + expr)
        c.c(*src, e, 0)
        d = c.obj("delay")
        c.c(e, 0, d, 0)
        c.c(d, 0, c.obj("s " + tick), 0)
        if stop:
            c.c(c.m(c.recv(stop), "stop"), 0, d, 0)
    return st


def Toast(text):
    return Send("ac-toast", "list " + text)


RNG = Call("ac-rng")
