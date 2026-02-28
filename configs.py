from os import path
from json import load
import typing

PROJECT_ROOT = path.dirname(path.abspath(__file__))

SOCIAL_MAPS = {
    "facebook": {
        "login": "https://web.facebook.com",
    }
}

# FOLDER PROFIL CHROME (Ini pengganti file json)
# Bot akan menyimpan semua data login di dalam folder ini
USER_DATA_DIR = path.join(PROJECT_ROOT, "facebook_profile_data")

def get_sources_list() -> typing.List:
    file_path = path.join(PROJECT_ROOT, "groups.json")
    if path.exists(file_path):
        with open(file_path, "r") as sources_file:
            return load(sources_file)
    return []