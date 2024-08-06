import os
import re


def get_files(dir: str, pattern: str) -> 'list[str]':

    p = re.compile(pattern, re.IGNORECASE)
    files = [s for s in os.listdir(dir) if p.match(s)]
    files.sort()
    return files
