import os
import os.path as p
import shutil
import warnings
import pickle
from abc import ABC, abstractmethod


class File(ABC):
    def __init__(self, path: str):
        self._path = path
        assert p.exists(self._path)
        assert p.isfile(self._path)

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return p.basename(self._path)

    @property
    def basename(self):
        return self.name.rsplit(".", 1)[0]

    @property
    def folder(self):
        return p.dirname(self._path)

    @property
    def end(self):
        return self.path.rsplit(".", 1)[-1]

    def save_to(self, path: str):
        folder = p.dirname(path)
        if not p.exists(folder):
            warnings.warn(f"{folder} is not existed. Created it.")
            os.makedirs(folder, exist_ok=False)
        shutil.copy(self._path, path)

    def __eq__(self, other):
        return self._path == other.path

    @abstractmethod
    def __enter__(self):
        return self._path

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    @classmethod
    @abstractmethod
    def create_on(cls, path: str):
        with open(path, "w") as f:
            f.write("")
        return File(path=path)


class Iterator:
    def __init__(self, root: str, file_class: type, *,
                 use_cache: bool = True, cache_file: str = None, validation: bool = False, file_config: dict = None):
        self.root = root
        assert len(os.listdir(root)) > 0
        self.file_class = file_class
        self.file_config = {} if file_config is None else file_config
        # create a tree from root
        if use_cache:
            if cache_file is None:
                cache_file = p.join(p.dirname(root), f"{p.basename(root)}.cache")
            if p.exists(cache_file):
                with open(cache_file, "rb") as f:
                    self.tree = pickle.load(f)
            else:  # there's no cache file
                self.tree = []
                self.scan_files(root=self.root, parent=self.tree)
                with open(cache_file, "wb") as f:
                    pickle.dump(self.tree, f)
        else:  # not use cache
            self.tree = []
            self.scan_files(root=self.root, parent=self.tree)
        # validation
        if use_cache and validation:
            for item in self:
                if not p.exists(item.path):
                    warnings.warn(f"File changed in {item.path}. Rescan files.")
                    self.tree.clear()
                    self.scan_files(root=self.root, parent=self.tree)
                    if use_cache:
                        with open(cache_file, "wb") as f:
                            pickle.dump(self.tree, f)
                    break  # have been rescanned
        # for resume processing
        self.num_finished_last = 0
        self.num_finished_this = 0

    def scan_files(self, root: str, parent: list):
        item_list = os.listdir(root)
        item_list.sort()
        for item in item_list:
            item = p.abspath(p.join(root, item))
            if p.isfile(item):
                file = self.file_class(item, **self.file_config)
                parent.append(file)
            elif p.isdir(item):
                child = []
                self.scan_files(root=item, parent=child)
                if len(child) == 0:
                    warnings.warn(f"{item} is an empty folder. Ignored.")
                    continue
                parent.append(child)
            else:  # cannot identify
                warnings.warn(f"{item} is not a file nor a folder. Ignored.")

    def traverse(self, tree: list):
        for item in tree:
            if isinstance(item, self.file_class):
                if self.num_finished_this < self.num_finished_last:
                    self.num_finished_this += 1
                    continue
                self.num_finished_this += 1
                yield item
            elif isinstance(item, list):
                yield from self.traverse(tree=item)
            else:  # error
                raise RuntimeError(f"Impossible type {type(item)}")

    def __iter__(self):
        self.num_finished_this = 0
        return self.traverse(tree=self.tree)

    @classmethod
    def load_from_cache(cls, root: str, cache_path: str):
        if not p.exists(cache_path):
            warnings.warn(f"Cache file {cache_path} does not exist. Created.")
            # noinspection PyArgumentList
            return cls(root=root)
        with open(cache_path, "rb") as f:
            obj = pickle.load(f)
        return obj

    def save_to_cache(self, cache_path: str):
        self.num_finished_last = self.num_finished_this
        with open(cache_path, "wb") as f:
            pickle.dump(self, f)
