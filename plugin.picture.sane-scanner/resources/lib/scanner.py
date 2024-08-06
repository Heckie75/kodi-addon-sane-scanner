import os
import re
import subprocess
import tempfile
import time

import xbmcaddon
import xbmcgui
import xbmcvfs
from resources.lib import fileutils

_SCANNER_MODES = [
    ["--mode", "Color"],
    ["--mode", "Gray"],
    ["--mode", "Gray"],
    ["--mode", "Lineart"]
]

_SCANNNER_RESOLUTIONS = [
    ["--resolution", "4800"],
    ["--resolution", "2400"],
    ["--resolution", "1200"],
    ["--resolution", "600"],
    ["--resolution", "300"],
    ["--resolution", "150"],
    ["--resolution", "100"],
    ["--resolution", "75"]
]

_SCANNER_FORMAT = [
    "png",
    "jpeg"
]

_SCANNER_DIMENSIONS = [
    [],
    ["-l", "0", "-t", "0", "-x", "216mm", "-y", "279mm"],
    ["-l", "0", "-t", "0", "-x", "210mm", "-y", "297mm"],
    ["-l", "0", "-t", "0", "-x", "148mm", "-y", "210mm"],
    ["-l", "0", "-t", "0", "-x", "105mm", "-y", "148mm"],
]


_SCANNED_IMG_PREFIX = "kodi-sane-scanner-img"


def find_scanner() -> None:

    addon = xbmcaddon.Addon()
    addon_dir = xbmcvfs.translatePath(addon.getAddonInfo('path'))

    p1 = subprocess.Popen(["scanimage", "-f" "%d %v %m %t%n"],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)

    out, err = p1.communicate()

    i = 0
    for match in re.finditer('([^ ]+) (.+)', out.decode("utf-8")):
        addon.setSetting("scanner_%i" %
                         i, f"{match.group(2)}|{match.group(1)}")
        i += 1

    p1.stdout.close()

    for j in range(i, 2):
        addon.setSetting("scanner_%i" % j, "")

    if i == 0:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32001),
                                      message=addon.getLocalizedString(32002),
                                      icon=f"{addon_dir}resources/assets/icon.png")
    else:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32003),
                                      message=addon.getLocalizedString(
                                          32004) % i,
                                      icon=f"{addon_dir}resources/assets/icon.png")


def _get_scanner() -> 'list[str]':

    addon = xbmcaddon.Addon()
    scanner = addon.getSettingInt("scanner_scanner")

    if scanner == 2:
        return None
    else:
        return addon.getSetting("scanner_%i" % scanner).split("|")


def scan():

    addon = xbmcaddon.Addon()

    def _get_format() -> str:

        return _SCANNER_FORMAT[addon.getSettingInt("scanner_format")]

    def _convert_to_monochrome(input_file):

        call = ["convert",
                "-monochrome",
                input_file,
                input_file
                ]

        p = subprocess.Popen(call, stdout=subprocess.PIPE)
        p.wait()
        p.stdout.close()

    call = ["scanimage",
            f"--format={_get_format()}",
            "--brightness", addon.getSetting("scanner_brightness"),
            "--contrast", addon.getSetting("scanner_contrast")
            ]

    _scanner = _get_scanner()
    if _scanner != None and len(_scanner) == 2:
        call += [f"--device-name={_scanner[1]}"]

    call += _SCANNER_DIMENSIONS[
        addon.getSettingInt("scanner_dimension")]
    call += _SCANNER_MODES[
        addon.getSettingInt("scanner_mode")]
    call += _SCANNNER_RESOLUTIONS[
        addon.getSettingInt("scanner_resolution")]

    tmp_file = os.path.join(tempfile.gettempdir(),
                            f"{_SCANNED_IMG_PREFIX}.{time.time()}.{_get_format()}")
    _file = open(tmp_file, "w")

    p = subprocess.Popen(call, stdout=_file, stderr=subprocess.PIPE)
    p.wait()
    _file.close()

    if addon.getSettingInt("scanner_mode") == 2:
        _convert_to_monochrome(tmp_file)


def get_scanned_files() -> 'list[str]':
    return fileutils.get_files(tempfile.gettempdir(), "^" + _SCANNED_IMG_PREFIX)


def delete_latest_scanned_file():

    scanned_files = get_scanned_files()
    os.remove(os.path.join(tempfile.gettempdir(), scanned_files[-1]))


def delete_scanned_files():

    scanned_files = get_scanned_files()
    for f in scanned_files:
        os.remove(os.path.join(tempfile.gettempdir(), f))


def lampoff():

    call = ["scanimage",
            "-n", "--lamp-switch=no"]

    _scanner = _get_scanner()
    if _scanner != None and len(_scanner) == 2:
        call += [f"--device-name={_scanner[1]}"]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()
