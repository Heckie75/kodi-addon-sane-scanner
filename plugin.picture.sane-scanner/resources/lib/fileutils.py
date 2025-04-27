import os
import re
import shutil
import unicodedata

_ENCODING = "utf-8"

_SPECIAL_CHARS = "ÄÖÜäöüß"
_TRANSLATIONS = ['Ae', 'Oe', 'Ue', 'ae', 'oe', 'ue', 'ss']


def encode(s: str) -> bytes:

    return bytes(s, _ENCODING)


def decode(b: bytes) -> str:

    return b.decode(_ENCODING)


def normalize(s: str) -> str:

    for i, c in enumerate(_SPECIAL_CHARS):
        s = s.replace(c, _TRANSLATIONS[i])

    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')


def get_files(dir: str, pattern: str) -> 'list[str]':

    p = re.compile(pattern, re.IGNORECASE)
    files = [decode(s) for s in os.listdir(encode(dir)) if p.match(decode(s))]
    files.sort()
    return files


def listdir(path: str) -> 'list[str]':

    return [decode(f) for f in os.listdir(encode(path))]


def rename(src: str, dst: str) -> None:

    os.rename(encode(src), encode(dst))


def move(src: str, dst: str) -> str:

    shutil.move(encode(src), encode(dst))  # TODO still encoding errors


def mkdir(path: str) -> None:

    os.mkdir(encode(path))


def isdir(path: str) -> bool:

    return os.path.isdir(encode(path))


def rmtree(path: str) -> None:

    shutil.rmtree(encode(path))


def remove(path: str) -> None:

    os.remove(encode(path))


def getmtime(path: str) -> float:

    return os.path.getmtime(encode(path))
