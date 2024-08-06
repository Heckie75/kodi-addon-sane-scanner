import os
import re
import shutil

import xbmc
import xbmcaddon
import xbmcgui

AUDIO = "audio"
VIDEO = "video"
PICTURE = "picture"
PDF = "pdf"
DRAW = "draw"
DOC = "doc"
SPREADSHEET = "spreadsheet"
PRESENTATION = "presentation"
FOLDER = "folder"
SCRIPT = "script"

def get_files_in_archive(path: str) -> 'list[tuple[str, str,str]]':

    files = os.listdir(path)
    result = list()
    for f in files:
        if f.startswith("."):
            continue
        fullpath = os.path.join(path, f)
        result.append((f, fullpath, get_file_type(fullpath)))

    return result


def get_real_path_in_archive(url: str) -> 'tuple[str,str,str]':

    addon = xbmcaddon.Addon()
    splitted_path = url.split("/")
    return os.path.sep.join([addon.getSetting("output_folder")] + splitted_path[2:]), os.path.sep.join([addon.getSetting("output_folder")] + splitted_path[2:-1]), splitted_path[-1]


def build_full_path(path: str) -> str:

    addon = xbmcaddon.Addon()
    return os.path.join(addon.getSetting("output_folder"), path)


def rename(url: str) -> str:

    addon = xbmcaddon.Addon()
    fullpath, archive, filename = get_real_path_in_archive(url)
    renamed_file = xbmcgui.Dialog().input(addon.getLocalizedString(32010),
                                          filename,
                                          xbmcgui.INPUT_ALPHANUM)

    if renamed_file != "":
        shutil.move(fullpath, os.path.join(archive, renamed_file))
        return _get_path_to_refresh(url=url, fullpath=fullpath)

    return None


def mkdir(url: str) -> str:

    addon = xbmcaddon.Addon()
    fullpath, archive, filename = get_real_path_in_archive(url)
    new_folder = xbmcgui.Dialog().input(addon.getLocalizedString(32089), "",
                                        xbmcgui.INPUT_ALPHANUM)

    if new_folder != "":
        os.mkdir(os.path.join(archive, new_folder))
        return _get_path_to_refresh(url=url, fullpath=fullpath)

    return None


def delete(url: str) -> str:

    addon = xbmcaddon.Addon()
    fullpath, _, file_to_delete = get_real_path_in_archive(url)
    isdir = os.path.isdir(fullpath)
    yes = xbmcgui.Dialog().yesno(addon.getLocalizedString(
        32000), addon.getLocalizedString(32087 if isdir else 32080) % file_to_delete)
    if yes:
        if os.path.isdir(fullpath):
            shutil.rmtree(fullpath)
        else:
            os.remove(fullpath)
        return _get_path_to_refresh(url=url, fullpath=fullpath)

    return None


def move(url: str) -> str:

    addon = xbmcaddon.Addon()
    fullpath, _, file_to_move = get_real_path_in_archive(url)
    target = xbmcgui.Dialog().browseSingle(
        type=3, heading=addon.getLocalizedString(32085) % file_to_move, shares="local")
    if target:
        shutil.move(fullpath, target)
        return _get_path_to_refresh(url=url, fullpath=fullpath)

    return None


def _get_path_to_refresh(url: str, fullpath: str) -> str:

    return url if os.path.isdir(fullpath) else os.path.sep.join(url.split(os.path.sep)[:-1])


def get_file_type(path: str) -> str:

    def _get_file_extension(path: str) -> str:

        m = re.match("^.+(\.[^\.]+)$", path.lower())
        if not m:
            return None

        else:
            return m.groups()[0]

    addon = xbmcaddon.Addon()
    if os.path.isdir(path):
        return FOLDER

    ext = _get_file_extension(path)
    soffice = addon.getSetting("soffice") == "true"
    if ext and ext in [".pdf"]:
        return PDF

    elif soffice and ext and ext in [".ini", ".sh", ".py", ".md", ".json", ".bat", ".yml", ".http"]:
        return SCRIPT

    elif ext and ext in [".doc", ".dot", ".odt", ".rtf", ".wpd", ".wps", ".txt", ".ott", ".docx", ".dotx", ".epub"]:
        return DOC

    elif soffice and ext and ext in [".csv", ".ods", ".xls", ".xlt", ".ots", ".xlsx", ".xltx"]:
        return SPREADSHEET

    elif soffice and ext and ext in [".ppt", ".odp", ".otp", ".pptx", ".potx"]:
        return PRESENTATION

    elif soffice and ext and ext in [".odg", ".pub", ".vdx", ".vsd", ".vsdx", ".odf", ".svg"]:
        return DRAW

    elif ext and (ext + "|") in xbmc.getSupportedMedia("music"):
        return AUDIO

    elif ext and (ext + "|") in xbmc.getSupportedMedia("video"):
        return VIDEO

    elif ext and (ext + "|") in xbmc.getSupportedMedia("picture"):
        return PICTURE

    return None
