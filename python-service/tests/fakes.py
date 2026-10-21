"""Small Firestore fake for testing owner scoping and transactional state changes."""
from copy import deepcopy
from google.api_core.exceptions import Conflict


class Snapshot:
    def __init__(self, reference):
        self.reference = reference
        self.id = reference.path.rsplit("/", 1)[-1]
        self.exists = reference.path in reference.db.data
        self.value = deepcopy(reference.db.data.get(reference.path))

    def to_dict(self):
        return deepcopy(self.value)


class Reference:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def collection(self, name):
        return Collection(self.db, f"{self.path}/{name}")

    def get(self, transaction=None):
        return Snapshot(self)

    def set(self, value, merge=False):
        self.db.data[self.path] = {**(self.db.data.get(self.path, {}) if merge else {}), **deepcopy(value)}

    def update(self, value):
        if self.path not in self.db.data:
            raise LookupError(self.path)
        self.set(value, merge=True)

    def create(self, value):
        if self.path in self.db.data:
            raise Conflict("exists")
        self.set(value)


class Collection:
    def __init__(self, db, path):
        self.db, self.path = db, path
        self.order, self.count = None, 1000

    def document(self, name):
        return Reference(self.db, f"{self.path}/{name}")

    def order_by(self, key, direction=None):
        self.order = key
        return self

    def limit(self, count):
        self.count = count
        return self

    def where(self, *, filter):
        self.field_filter = filter
        return self

    def stream(self):
        values = [Snapshot(Reference(self.db, key)) for key in self.db.data
                  if key.startswith(self.path + "/") and key.count("/") == self.path.count("/") + 1]
        field_filter = getattr(self, "field_filter", None)
        if field_filter:
            values = [item for item in values if item.value.get(field_filter.field_path) == field_filter.value]
        if self.order:
            values.sort(key=lambda item: item.value.get(self.order, ""), reverse=True)
        return values[:self.count]


class Transaction:
    def set(self, reference, value, **kwargs):
        reference.set(value, **kwargs)

    def update(self, reference, value):
        reference.update(value)

    def commit(self):
        pass


class MemoryFirestore:
    def __init__(self):
        self.data = {}

    def collection(self, name):
        return Collection(self, name)

    def transaction(self):
        return Transaction()

    def batch(self):
        return Transaction()
