from .iterator import File
from .iterator import Iterator
from PIL import Image


class ImageFile(File):
    def __init__(self, path: str, validation: bool = False):
        if validation:
            assert self.validation(path), f"{path} is not an image."
        super().__init__(path=path)

    def validation(self, path):
        try:  # validation
            image = Image.open(path)
            image.verify()
            return True
        except (IOError, SyntaxError) as e:
            return False

    @property
    def img(self):
        f = open(self.path, 'rb')
        img = Image.open(f).convert("RGB")
        img_bytes = img.tobytes()
        real_img = Image.frombytes(img.mode, img.size, img_bytes)
        f.close()
        return real_img

    def show(self):
        self.img.show()

    def __enter__(self):
        return self.img

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    @classmethod
    def create_on(cls, path: str):
        raise RuntimeError("ImageFile cannot be created.")


class ImageIterator(Iterator):
    def __init__(self, root, **kwargs):
        super().__init__(root=root, file_class=ImageFile, **kwargs)
