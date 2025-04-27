import os
import re
import subprocess
import tempfile

import xbmc
import xbmcaddon
from resources.lib import fileutils
from resources.lib.archive import (DOC, DRAW, PDF, PRESENTATION, SCRIPT,
                                   SPREADSHEET)

_PDF_PREVIEW_FILE = "kodi-sane-scanner-pdf"

_PREVIEW_RESOLUTIONS = [
    "4800",
    "2400",
    "1200",
    "600",
    "300",
    "150",
    "100",
    "75"
]


def _get_preview_files() -> 'list[str]':
    return fileutils.get_files(tempfile.gettempdir(), "^" + _PDF_PREVIEW_FILE)


def convert_for_preview(path: str, filename: str, type_: str) -> 'list[str]':

    def _convert_to_pdf(path: str, filename: str) -> 'tuple[str, str]':

        fullpath = os.path.join(path, filename)
        call = ["soffice", "--convert-to", "pdf",
                "--outdir", tempfile.gettempdir(), fileutils.encode(fullpath)]
        p = subprocess.Popen(call, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        p.stdout.close()
        m = re.match(
            r"^convert .+ -> .+/([^/]+) using filter : .+", fileutils.decode(out))
        if m:
            outfile = m.groups()[0]

        return tempfile.gettempdir(), outfile

    def _convert_from_pdf(path: str, filename: str):
        call = ["convert",
                "-density", _PREVIEW_RESOLUTIONS[
                    addon.getSettingInt("archive_resolution")],
                "-quality", "90",
                "-background", "white", "-alpha", "background", "-alpha", "off",
                fileutils.encode(os.path.join(path, filename)),
                fileutils.encode(os.path.join(tempfile.gettempdir(),
                                              f"{_PDF_PREVIEW_FILE}.{filename}.png"))
                ]

        p = subprocess.Popen(call, stdout=subprocess.PIPE)
        p.wait()
        p.stdout.close()

    addon = xbmcaddon.Addon()
    _clean_preview_files()
    if type_ in [DOC, DRAW, PDF, PRESENTATION, SPREADSHEET, SCRIPT]:
        path, filename = _convert_to_pdf(path, filename)
        _convert_from_pdf(path, filename)
        fileutils.remove(os.path.join(path, filename))
    else:
        _convert_from_pdf(path, filename)

    return _get_preview_files()


def _clean_preview_files() -> None:

    for f in _get_preview_files():
        fileutils.remove(os.path.join(tempfile.gettempdir(), f))


def preview(path: str) -> None:

    tokens = path.split("/")[1:]
    url = os.path.join(tempfile.gettempdir(), tokens[-1])
    xbmc.executebuiltin(f"ShowPicture({url})")
