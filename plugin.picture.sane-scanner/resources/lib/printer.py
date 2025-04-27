import os
import subprocess

import xbmcaddon
import xbmcgui
import xbmcvfs
from resources.lib import archive, fileutils


def find_printer() -> None:

    addon = xbmcaddon.Addon()
    addon_dir = xbmcvfs.translatePath(addon.getAddonInfo('path'))

    p1 = subprocess.Popen(["lpstat", "-e"],
                          stdout=subprocess.PIPE)
    out, err = p1.communicate()

    i = 0
    for printer in fileutils.decode(out).split("\n"):
        addon.setSetting("printer_%i" % (i + 1), printer)
        i += 1

    p1.stdout.close()

    for j in range(i, 5):
        addon.setSetting("printer_%i" % (j + 1), "")

    if i == 0:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32005),
                                      message=addon.getLocalizedString(32006),
                                      icon=f"{addon_dir}resources/assets/icon.png")
    else:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32007),
                                      message=addon.getLocalizedString(
                                          32008) % (i - 1),
                                      icon=f"{addon_dir}resources/assets/icon.png")


def get_printer() -> str:

    addon = xbmcaddon.Addon()
    printer = addon.getSettingInt("output_printer")
    return addon.getSetting("printer_%i" % printer) if printer else ""


def print_(folder: str, filename: str) -> None:

    addon = xbmcaddon.Addon()

    type_ = archive.get_file_type(filename)
    if type_ in [archive.PDF, archive.DOC, archive.PRESENTATION, archive.DRAW, archive.SPREADSHEET, archive.SCRIPT, archive.PICTURE]:
        call = ["soffice", "--pt",
                get_printer(), fileutils.encode(os.path.join(folder, filename))]

    elif type_ == archive.PDF:
        call = ["lp",
                "-t", f"{addon.getLocalizedString(32000)}: {fileutils.encode(filename)}",
                ]

        if get_printer() != "":
            call += ["-d", get_printer()]

        call += [fileutils.encode(os.path.join(folder, filename))]

    else:
        return

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()
