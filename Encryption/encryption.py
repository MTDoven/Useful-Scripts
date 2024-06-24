from datetime import datetime
import warnings
import hashlib
import pickle
import pprint
import atexit
import base64
import os
import io


def get_hash_key(key: str = "0") -> bytes:
    hash_object = hashlib.sha512()
    hash_object.update(key.encode())
    hash_hex = hash_object.hexdigest()
    key = bytes(hash_hex.encode())
    return key


def encode_to_base64(string, hash_key):
    content = string.encode('utf-8')
    content = encrypt(content=content, hash_key=hash_key)
    content = base64.b64encode(content)
    result = content.decode('utf-8')
    if len(result) > 255:
        raise ValueError(f"Encrypted string too long {len(result)}")
    return result


def decode_from_base64(base64_string, hash_key):
    content = base64.b64decode(base64_string)
    content = encrypt(content=content, hash_key=hash_key)
    result = content.decode('utf-8')
    return result


def encrypt(content: bytes, hash_key: bytes, return_bytearray=False) -> bytes:
    original_length = len(content)
    if len(content) <= len(hash_key):
        final_key = hash_key[:len(content)]
        final_content = content
    else:  # len(content) > len(hash_key):
        patch_length = len(hash_key)
        total_length = len(content) // patch_length * patch_length + patch_length
        patch_number = total_length // patch_length
        final_key = hash_key * patch_number
        final_content = content + bytes(total_length-len(content))
    assert len(final_content) == len(final_key), \
        f"final key should be the same length as content, but final_content:{len(content)}, final_key{len(final_key)}."
    final_key = bytearray(final_key)
    final_content = bytearray(final_content)
    result = bytearray(final_content ^ final_key for final_content, final_key in zip(final_content, final_key))
    if return_bytearray:
        return result[:original_length]
    else:  # return bytes
        return bytes(result[:original_length])


class EncryptedFile:
    hash_key: bytes = get_hash_key(key="0")

    def __init__(self, diction: dict, auto_save=True) -> None:
        self._diction = diction
        self._info_diction = self._diction.copy()
        del self._info_diction["data"]
        del self._info_diction["log"]
        self._open_file_path = None
        if auto_save:
            atexit.register(self.save)

    @classmethod
    def set_key(cls, key: str = "0") -> None:
        cls.hash_key = get_hash_key(key=key)

    @staticmethod
    def encrypt_one_file(file_path: str, output_path: str = None, delete_origin=False) -> "EncryptedFile":
        if output_path is None:
            file_name = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            father_path = os.path.basename(dir_path)
            hash_hex = encode_to_base64(string=file_name, hash_key=EncryptedFile.hash_key)
            output_path = os.path.join(dir_path, hash_hex+".enpt")
        with open(file_path, "rb") as f:
            buffer = f.read()
        file_name = os.path.basename(file_path)
        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        diction = {"data": buffer,
                   "name": file_name,
                   "source": file_path,
                   "log": f"[{time_now}][encrypt] encrypted {file_name} from {file_path}; "}
        self = EncryptedFile(diction=diction, auto_save=False)
        self._open_file_path = output_path
        self.save(save_path=output_path)
        if delete_origin:
            os.remove(file_path)
        return self

    @staticmethod
    def open(file_path: str, auto_save=True) -> "EncryptedFile":
        with open(file_path, "rb") as f:
            buffer = f.read()
        buffer = encrypt(buffer, hash_key=EncryptedFile.hash_key)
        diction = pickle.load(io.BytesIO(buffer))
        assert isinstance(diction, dict), f"file should be a dict, but {type(diction)}."
        self = EncryptedFile(diction, auto_save=auto_save)
        self._open_file_path = file_path
        return self

    def save(self, save_path: str = None) -> None:
        if save_path is None:
            save_path = self._open_file_path
        dirname = os.path.dirname(save_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=False)
        buffer = io.BytesIO()
        pickle.dump(self._diction, buffer)
        buffer.seek(0)
        buffer = encrypt(buffer.read(), hash_key=self.hash_key)
        with open(save_path, "wb") as f:
            f.write(buffer)

    def update(self, **kwargs) -> None:
        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for key, value in kwargs.items():
            if value is not None:  # update
                self._diction[key] = value
                if key != "data":
                    self._info_diction[key] = value
                self._diction["log"] += f"[{time_now}][update] update information of {key} with {value}; "
            else:  # delete
                assert key != "data", f"data should not be deleted."
                if self._diction.get(key) is None:
                    warnings.warn(f"{key} is not in this file's info.", UserWarning)
                    return
                self._diction["log"] += f"[{time_now}][delete] delete information of {key} with {self._diction[key]}; "
                del self._diction[key]
                del self._info_diction[key]

    def save_original_file(self, save_path: str = None) -> None:
        if save_path is None:
            save_path = os.path.join(os.path.dirname(self._open_file_path), self._diction["name"])
        dirname = os.path.dirname(save_path)
        if not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=False)
        with open(save_path, "wb") as f:
            f.write(self._diction["data"])
        time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._diction["log"] += f"[{time_now}][save_original_file] save to {save_path}; "

    def log_clear(self) -> None:
        self._diction["log"] = ""

    def get_log(self) -> str:
        return self._diction["log"]

    @property
    def file(self) -> io.BytesIO:
        return io.BytesIO(self._diction["data"])

    @property
    def info(self) -> dict:
        return self._info_diction

    def __repr__(self):
        return f"<EncryptedFile: {self._open_file_path}>"

    def __str__(self):
        output = io.StringIO()
        pprint.pprint(f"<EncryptedFile:{self._open_file_path}>", stream=output)
        pprint.pprint(self._info_diction, stream=output)
        return output.getvalue()
