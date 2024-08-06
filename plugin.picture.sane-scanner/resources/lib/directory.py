import datetime
import os
import tempfile

import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from resources.lib import archive, preview, printer, scanner


def _build_directory(path: str) -> 'list[dict]':

    addon = xbmcaddon.Addon()
    addon_dir = xbmcvfs.translatePath(addon.getAddonInfo('path'))

    def _build_root() -> 'list[dict]':

        scanned_files = scanner.get_scanned_files()

        entries = [
            {
                "path": "/",
                "name": addon.getLocalizedString(32012),
                "icon": "icon_scan",
                "exec": ["scan"],
                "msg": addon.getLocalizedString(32013),
                "node": []
            }
        ]

        if len(scanned_files) > 0:
            entries += [
                {
                    "path": "/",
                    "name": addon.getLocalizedString(32014),
                    "icon": "icon_scan2pdf",
                    "exec": ["scan2pdf"],
                    "msg": addon.getLocalizedString(32015),
                    "node": []
                }
            ]

        if len(scanned_files) > 0 and addon.getSetting("output_email") == "true":
            entries += [
                {
                    "path": "/",
                    "name": addon.getLocalizedString(32016),
                    "icon": "icon_scan2email",
                    "exec": ["scan2email"],
                    "msg": addon.getLocalizedString(32017),
                    "node": []
                }
            ]

        if len(scanned_files) > 0 and addon.getSettingInt("output_printer") != 0:
            entries += [
                {
                    "path": "/",
                    "name": addon.getLocalizedString(32018) % printer.get_printer(),
                    "icon": "icon_scan2print",
                    "exec": ["scan2print"],
                    "msg": addon.getLocalizedString(32019) % printer.get_printer(),
                    "node": []
                }
            ]

        i = 0
        for f in scanned_files:
            i += 1
            entries += [
                {
                    "path": f"/{f}",
                    "name": addon.getLocalizedString(32020) % i,
                    "image": os.path.join(tempfile.gettempdir(), f),
                    "exec": ["preview"]
                }
            ]

        if len(scanned_files) > 0:
            entries += [
                {
                    "path": "/",
                    "name": addon.getLocalizedString(32021),
                    "icon": "icon_undo",
                    "exec": ["undo"],
                    "msg": addon.getLocalizedString(32022),
                    "node": []
                },
                {
                    "path": "/",
                    "name": addon.getLocalizedString(32023),
                    "icon": "icon_trash",
                    "exec": ["clean"],
                    "msg": addon.getLocalizedString(32024),
                    "node": []
                }
            ]

        if addon.getSetting("archive") == "true":
            entries += [
                {
                    "path": "archive",
                    "name": addon.getLocalizedString(32025),
                    "node": []
                }
            ]

        return entries

    def _build_archive(path: str) -> 'list[dict]':

        def _get_icon_image(path: str, ext: str) -> 'tuple[str,str]':

            if ext == archive.AUDIO:
                return "icon_music", None

            elif ext == archive.PICTURE:
                return None, path

            elif ext == archive.VIDEO:
                return "icon_video", None

            elif ext == archive.PDF:
                return "icon_pdf", None

            elif ext == archive.SCRIPT:
                return "icon_script", None

            elif ext == archive.DOC:
                return "icon_doc", None

            elif ext == archive.SPREADSHEET:
                return "icon_spreadsheet", None

            elif ext == archive.DRAW:
                return "icon_draw", None

            elif ext == archive.PRESENTATION:
                return "icon_presentation", None

            elif ext == archive.FOLDER:
                return None, None

            return "icon_file", None

        archive_operations = addon.getSetting("archive_operations") == "true"
        soffice = addon.getSetting("soffice") == "true"

        files_w_types = archive.get_files_in_archive(path)

        entries = list()

        for f in files_w_types:

            icon, image = _get_icon_image(f[1], f[2])
            entry = {
                "path": f[0],
                "name": f[0],
                "date": datetime.datetime.fromtimestamp(os.path.getmtime(filename=f[1])),
                "file": True
            }

            if f[2]:
                entry["node"] = []

            if icon:
                entry["icon"] = icon
            elif image:
                entry["image"] = image

            if f[2] in [archive.AUDIO, archive.VIDEO]:
                entry["exec"] = ["play"]
                entry["contextItems"] = [
                    (addon.getLocalizedString(32081), "email"),
                    (addon.getLocalizedString(32010), "rename"),
                    (addon.getLocalizedString(32084), "move"),
                    (addon.getLocalizedString(32011), "delete"),
                    (addon.getLocalizedString(32089), "mkdir")
                ] if archive_operations else []
            elif f[2] == archive.PICTURE:
                entry["exec"] = ["show"]
                entry["contextItems"] = [
                    (addon.getLocalizedString(32081), "email"),
                    (addon.getLocalizedString(32010), "rename"),
                    (addon.getLocalizedString(32084), "move"),
                    (addon.getLocalizedString(32011), "delete"),
                    (addon.getLocalizedString(32089), "mkdir")
                ] if archive_operations else []

                if archive_operations and soffice:
                    entry["contextItems"].insert(1, (addon.getLocalizedString(32082), "print"))

            elif f[2] in [archive.PDF, archive.DOC, archive.PRESENTATION, archive.DRAW, archive.SPREADSHEET, archive.SCRIPT]:
                entry["contextItems"] = [
                    (addon.getLocalizedString(32081), "email"),
                    (addon.getLocalizedString(32082), "print"),
                    (addon.getLocalizedString(32010), "rename"),
                    (addon.getLocalizedString(32084), "move"),
                    (addon.getLocalizedString(32011), "delete"),
                    (addon.getLocalizedString(32089), "mkdir")
                ] if archive_operations else []
            elif f[2] == archive.FOLDER:
                entry["contextItems"] = [
                    (addon.getLocalizedString(32079), "rename"),
                    (addon.getLocalizedString(32088), "move"),
                    (addon.getLocalizedString(32086), "delete"),
                    (addon.getLocalizedString(32089), "mkdir")
                ] if archive_operations else []
            else:
                entry["contextItems"] = [
                    (addon.getLocalizedString(32081), "email"),
                    (addon.getLocalizedString(32010), "rename"),
                    (addon.getLocalizedString(32084), "move"),
                    (addon.getLocalizedString(32011), "delete"),
                    (addon.getLocalizedString(32089), "mkdir")
                ] if archive_operations else []

            entries.append(entry)

        return [
            {
                "path": "archive",
                "name": addon.getLocalizedString(32025),
                "node": entries
            }
        ]

    def _preview(path: str, filename: str, type_: str) -> 'list[dict]':

        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32000),
                                      message=addon.getLocalizedString(32009),
                                      icon=f"{addon_dir}resources/assets/icon.png")

        return [
            {
                "path": "archive",
                "name": addon.getLocalizedString(32025),
                "node": [
                    {
                        "path": f"/{f}",
                        "name": addon.getLocalizedString(32026) % (i + 1),
                        "image": os.path.join(tempfile.gettempdir(), f),
                        "exec": ["preview"]
                    } for i, f in enumerate(preview.convert_for_preview(path, filename, type_))]
            }
        ]

    splitted_path = path.split(os.path.sep)
    splitted_path.pop(0)

    entries = []

    if path == "/":
        entries = _build_root()

    elif path == "/archive":
        entries = _build_archive(addon.getSetting("output_folder"))

    elif path.startswith("/archive/"):

        fullpath, path, filename = archive.get_real_path_in_archive(path)
        type_ = archive.get_file_type(fullpath)
        if filename and type_ in [archive.PDF, archive.DOC, archive.PRESENTATION, archive.DRAW, archive.SPREADSHEET, archive.SCRIPT]:
            entries = _preview(path=path, filename=filename, type_=type_)

        elif type_ == archive.FOLDER:
            entries = _build_archive(fullpath)

    return [
        {
            "path": "",
            "node": entries
        }
    ]


def _get_subdirectory_by_path(directory_: 'list[dict]', path: str) -> str:

    if path == "/":
        return directory_[0]

    tokens = path.split("/")[1:]
    directory = directory_[0]

    while len(tokens) > 0:
        path = tokens.pop(0)
        for node in directory["node"]:
            if node["path"] == path:
                directory = node
                break

    return directory


def browse(path: str, handle: int) -> None:

    addon = xbmcaddon.Addon()
    addon_dir = xbmcvfs.translatePath(addon.getAddonInfo('path'))

    def _build_param_string(param: str, values: 'list[str]', current="") -> str:

        if not values:
            return current

        for v in values:
            current += "?" if len(current) == 0 else "&"
            current += param + "=" + str(v)

        return current

    def _add_list_item(entry: str, path: str) -> 'dict':

        sort_methods = {}

        if path == "/":
            path = ""

        item_path = path + "/" + entry["path"]

        param_string = ""
        if "exec" in entry:
            param_string = _build_param_string(
                param="exec",
                values=entry["exec"],
                current=param_string)

        if "param" in entry:
            param_string = _build_param_string(
                param=entry["param"][0],
                values=[entry["param"][1]],
                current=param_string)

        if "msg" in entry:
            param_string = _build_param_string(
                param="msg",
                values=[entry["msg"]],
                current=param_string)

        if "node" in entry:
            is_folder = True
        else:
            is_folder = False

        label = entry["name"]

        if "image" in entry:
            icon_file = entry["image"]
        elif "icon" in entry:
            icon_file = os.path.join(addon_dir,
                                     "resources", "assets",
                                     entry["icon"] + ".png")
        else:
            icon_file = None

        li = xbmcgui.ListItem(label)
        li.setArt({"icon": icon_file})

        if "image" in entry:
            li.setAvailableFanart([
                {"image": icon_file, "preview": icon_file}
            ])

        if "date" in entry and entry["date"]:
            if "setDateTime" in dir(li):  # available since Kodi v20
                li.setDateTime(entry["date"].strftime("%Y-%m-%dT%H:%M:%SZ"))
                sort_methods[xbmcplugin.SORT_METHOD_DATE] = True

        if "file" in entry and entry["file"]:
            sort_methods[xbmcplugin.SORT_METHOD_FILE] = True

        if "contextItems" in entry:
            commands = []
            for ci in entry["contextItems"]:
                p = _build_param_string(
                    param="exec",
                    values=[ci[1]],
                    current="")
                url = "plugin://%s%s%s" % (addon.getAddonInfo("id"),
                                           item_path, p)
                commands.append((ci[0], 'RunPlugin(%s)' % url))

            li.addContextMenuItems(commands)

        xbmcplugin.addDirectoryItem(handle=handle,
                                    listitem=li,
                                    url="plugin://" + addon.getAddonInfo("id")
                                    + item_path
                                    + param_string,
                                    isFolder=is_folder)

        return sort_methods

    directory_ = _build_directory(path)

    sort_methods = {}
    directory = _get_subdirectory_by_path(directory_, path)
    for entry in directory["node"]:
        sort_methods = _add_list_item(entry, path)

    for sort_method in sort_methods:
        xbmcplugin.addSortMethod(handle, sort_method)

    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
