"""Stubs that replace one component of a task program with something that prints the same."""
import marshal
import os
import sys
import types


class Ctx:
    def __init__(self, cache_dir, record):
        self.cache_dir = cache_dir
        self.record = record

    def _path(self, name):
        return os.path.join(self.cache_dir, name + ".marshal")

    def save(self, name, obj):
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(self._path(name), "wb") as f:
            marshal.dump(obj, f)

    def load(self, name):
        # One read, then loads: marshal.load on the file reads it piecemeal, about 7x slower.
        with open(self._path(name), "rb") as f:
            return marshal.loads(f.read())


def resolve(app, dotted):
    *path, attr = dotted.split(".")
    owner = app
    for p in path:
        owner = getattr(owner, p)
    return owner, attr


def frozen(value):
    # A copy taken at return time, so a caller mutating the value later cannot change the recording.
    return marshal.loads(marshal.dumps(value))


class Stub:
    def before_import(self, ctx):
        pass

    def after_import(self, app, ctx):
        pass

    def finish(self, ctx):
        pass


class Replace(Stub):
    """Swap a function for a cheap hand-written equivalent."""

    def __init__(self, target, fn):
        self.target, self.fn = target, fn

    def after_import(self, app, ctx):
        if not ctx.record:
            owner, attr = resolve(app, self.target)
            setattr(owner, attr, self.fn)


class Replay(Stub):
    """Record a function's return values in a real run, then return them in order without running it.

    With fake_module, the module that owns the function is never imported in a stubbed run: a bare
    module holding only the replayer takes its place in sys.modules.
    """

    def __init__(self, target, fake_module=None):
        self.target, self.fake_module = target, fake_module
        self.name = target.replace(".", "_")
        self.values = []

    def _replayer(self, ctx):
        it = iter(ctx.load(self.name))

        def replay(*args, **kwargs):
            return next(it)
        return replay

    def before_import(self, ctx):
        if not ctx.record and self.fake_module:
            mod = types.ModuleType(self.fake_module)
            setattr(mod, self.target.rsplit(".", 1)[1], self._replayer(ctx))
            sys.modules[self.fake_module] = mod

    def after_import(self, app, ctx):
        owner, attr = resolve(app, self.target)
        if ctx.record:
            real, seen = getattr(owner, attr), self.values

            def recorder(*args, **kwargs):
                value = real(*args, **kwargs)
                seen.append(frozen(value))
                return value
            setattr(owner, attr, recorder)
        elif not self.fake_module:
            setattr(owner, attr, self._replayer(ctx))

    def finish(self, ctx):
        if ctx.record:
            ctx.save(self.name, self.values)


class ReplayWrite(Stub):
    """For a function fn(obj, out) whose whole effect is text written to out: record the text."""

    def __init__(self, target):
        self.target = target
        self.name = target.replace(".", "_")
        self.text = None

    def after_import(self, app, ctx):
        import io
        owner, attr = resolve(app, self.target)
        if ctx.record:
            real = getattr(owner, attr)

            def recorder(obj, out):
                buf = io.StringIO()
                real(obj, buf)
                self.text = buf.getvalue()
                out.write(self.text)
            setattr(owner, attr, recorder)
        else:
            text = ctx.load(self.name)
            setattr(owner, attr, lambda obj, out: out.write(text))

    def finish(self, ctx):
        if ctx.record:
            ctx.save(self.name, self.text)


class Hook(Stub):
    """Run a function before the program is imported (for global switches such as logging.disable)."""

    def __init__(self, fn):
        self.fn = fn

    def before_import(self, ctx):
        if not ctx.record:
            self.fn()


class ReplayAfter(Stub):
    """Replay for a function whose input must still be consumed or waited for.

    A stubbed run calls before(*args) first (drain an iterator, wait for a child process), so the
    work that input carries still happens, then returns the next recorded value. save turns a
    value into something marshal can store and rebuild turns it back. With neither, it is Replay
    reading its recording in one read (the hard tier uses it in place of Replay).
    """

    def __init__(self, target, before=None, save=frozen, rebuild=None):
        self.target, self.before, self.save, self.rebuild = target, before, save, rebuild
        self.name = target.replace(".", "_")
        self.values = []

    def after_import(self, app, ctx):
        owner, attr = resolve(app, self.target)
        if ctx.record:
            real, seen = getattr(owner, attr), self.values

            def recorder(*args, **kwargs):
                value = real(*args, **kwargs)
                seen.append(self.save(value))
                return value
            setattr(owner, attr, recorder)
            return
        it = iter(ctx.load(self.name))
        before, rebuild = self.before, self.rebuild

        def replay(*args, **kwargs):
            if before:
                before(*args)
            v = next(it)
            return rebuild(v) if rebuild else v
        setattr(owner, attr, replay)

    def finish(self, ctx):
        if ctx.record:
            ctx.save(self.name, self.values)


class ReplayLazy(Stub):
    """For a function that returns a lazy iterator: record project(item) for each item the
    consumer pulls; a stubbed run returns map(rebuild, recorded items) without running it."""

    def __init__(self, target, project, rebuild):
        self.target, self.project, self.rebuild = target, project, rebuild
        self.name = target.replace(".", "_")
        self.values = []

    def after_import(self, app, ctx):
        owner, attr = resolve(app, self.target)
        if ctx.record:
            real, seen, project = getattr(owner, attr), self.values, self.project

            def recorder(*args, **kwargs):
                items = []
                seen.append(items)
                for item in real(*args, **kwargs):
                    items.append(project(item))
                    yield item
            setattr(owner, attr, recorder)
            return
        it = iter(ctx.load(self.name))
        rebuild = self.rebuild
        setattr(owner, attr, lambda *args, **kwargs: map(rebuild, next(it)))

    def finish(self, ctx):
        if ctx.record:
            ctx.save(self.name, self.values)
