from stubkit import ReplayAfter, Stub


class _Recording:
    def __init__(self, proc, sink):
        self.proc, self.sink = proc, sink

    def communicate(self):
        out, err = self.proc.communicate()
        self.sink.append(out)
        return out, err

    @property
    def returncode(self):
        return self.proc.returncode


class _Done:
    returncode = 0

    def __init__(self, out):
        self.out = out

    def communicate(self):
        return self.out, None


class Spawn(Stub):
    """start_indexer without the child: a finished process whose output is the recorded one."""

    def __init__(self):
        self.outs = []

    def after_import(self, app, ctx):
        real = app.start_indexer
        if ctx.record:
            app.start_indexer = lambda path: _Recording(real(path), self.outs)
        else:
            it = iter(ctx.load("start_indexer"))
            app.start_indexer = lambda path: _Done(next(it))

    def finish(self, ctx):
        if ctx.record:
            ctx.save("start_indexer", self.outs)


STUBS = {
    "start_indexer": Spawn(),
    # still waits for the child, so its work is not cut short
    "read_postings": ReplayAfter("read_postings", before=lambda proc: proc.communicate()),
    "edit_pairs": ReplayAfter("edit_pairs"),
    "load_titles": ReplayAfter("load_titles"),
}
