from typing import Union
from .encryption import *
import os


def encrypt_items(items: Union[str, list[str]], delete_origin=False, rename_dir=False) -> None:
    if isinstance(items, list):
        for item in items:
            encrypt_items(item, delete_origin=delete_origin)
        return
    if not os.path.exists(items):
        raise FileNotFoundError(f"{items} not found.")
    # assert isinstance(items, str)
    if os.path.isfile(items):
        if items.endswith('.enpt'):
            return
        EncryptedFile.encrypt_one_file(file_path=items, delete_origin=delete_origin)
        print(f"Finished encrypting: {items}")
    else:  # items is a dir
        dir_name = items
        items = [os.path.join(items, item) for item in os.listdir(items)]
        encrypt_items(items, delete_origin=delete_origin)
        if rename_dir:
            new_dir_name = encode_to_base64(os.path.basename(dir_name), hash_key=EncryptedFile.hash_key)
            new_dir_name = os.path.join(os.path.dirname(dir_name), new_dir_name)
            os.rename(dir_name, new_dir_name)


def decrypt_items(items: Union[str, list[str]], delete_origin=False, rename_dir=False) -> None:
    if isinstance(items, list):
        for item in items:
            decrypt_items(item, delete_origin=delete_origin)
        return
    if not os.path.exists(items):
        raise FileNotFoundError(f"{items} not found.")
    # assert isinstance(items, str)
    if os.path.isfile(items):
        if items.endswith('.enpt'):
            file = EncryptedFile.open(file_path=items, auto_save=False)
            file.save_original_file()
            print(f"Finished decrypting: {items} to {file.info['name']}.")
            if delete_origin:
                os.remove(items)
    else:  # items is a dir
        dir_name = items
        items = [os.path.join(items, item) for item in os.listdir(items)]
        decrypt_items(items, delete_origin=delete_origin)
        if rename_dir:
            new_dir_name = decode_from_base64(os.path.basename(dir_name), hash_key=EncryptedFile.hash_key)
            new_dir_name = os.path.join(os.path.dirname(dir_name), new_dir_name)
            os.rename(dir_name, new_dir_name)
