import os.path
import warnings
from pprint import pprint
from .iterator import File
from .iterator import Iterator
import json


class JsonFile(File):
    def __init__(self, path, validation: bool = False):
        if validation:
            assert self.validation(path), f"{path} is not an json file."
        if not os.path.exists(path):
            self.create_on(path)
        super().__init__(path=path)

    def validation(self, path):
        try:  # validation
            with self as f:
                pass
        except (IOError, EOFError) as e:
            return False

    @property
    def diction(self):
        this_diction = {}
        with self as d:
            this_diction.update(d)
        return this_diction

    def show(self):
        pprint(self.diction)

    def __enter__(self):
        with open(self.path, "r") as f:
            self.content = json.load(f)
        return self.content

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            with open(self.path, "w") as f:
                json.dump(self.content, f, indent=2)
            del self.content
        return False

    @classmethod
    def create_on(cls, path: str):
        if os.path.exists(path):
            warnings.warn(f"{path} have been existed.")
        if not path.endswith(".json"):
            path = path.join([".json"])
        with open(path, "w") as f:
            f.write("{}")
        return JsonFile(path=path)


class JsonIterator(Iterator):
    def __init__(self, root, **kwargs):
        super().__init__(root=root, file_class=JsonFile, **kwargs)
