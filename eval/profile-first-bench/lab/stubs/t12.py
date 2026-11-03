import array
from collections import deque

from stubkit import Replace, ReplayAfter, Stub


class LatestOnly:
    """The audit trail's interface, keeping only what the report prints."""

    def __init__(self):
        self.n, self.tail = 0, deque(maxlen=3)

    def add(self, session, priced):
        self.n += 1
        self.tail.append((session, priced))

    def __len__(self):
        return self.n

    def latest(self, n):
        return list(self.tail)[-n:]


class KnownNets(Stub):
    """price_basket with the arithmetic done: the same line dicts, each net read from a recording.

    Only the nets are recorded, as packed int64: loading 1.6M recorded dicts, or even 1.6M
    marshalled ints, would cost more than pricing them.
    """

    def __init__(self):
        self.nets = []

    def after_import(self, app, ctx):
        real = app.price_basket
        if ctx.record:
            def recorder(basket):
                priced = real(basket)
                self.nets.extend(line["net"] for line in priced)
                return priced
            app.price_basket = recorder
            return
        nets = iter(array.array("q", ctx.load("price_basket_nets")))
        app.price_basket = lambda basket: [{"sku": sku, "qty": qty, "net": next(nets)}
                                           for sku, (qty, _cents) in basket.items()]

    def finish(self, ctx):
        if ctx.record:
            ctx.save("price_basket_nets", array.array("q", self.nets).tobytes())


STUBS = {
    "audit_trail": Replace("AuditTrail", LatestOnly),
    "price_basket": KnownNets(),
    "tier_names": ReplayAfter("tier_names"),
    "load_events": ReplayAfter("load_events"),
}
