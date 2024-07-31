import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

_IMG_FILE = "kodi-sane-scanner-img"
_PDF_PREVIEW_FILE = "kodi-sane-scanner-pdf"

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

_ARCHIVE_RESOLUTIONS = [
    "4800",
    "2400",
    "1200",
    "600",
    "300",
    "150",
    "100",
    "75"
]

_SCANNER_DIMENSIONS = [
    [],
    ["-l", "0", "-t", "0", "-x", "216mm", "-y", "279mm"],
    ["-l", "0", "-t", "0", "-x", "210mm", "-y", "297mm"],
    ["-l", "0", "-t", "0", "-x", "148mm", "-y", "210mm"],
    ["-l", "0", "-t", "0", "-x", "105mm", "-y", "148mm"],
]

_SCANNER_FORMAT = [
    "png",
    "jpeg"
]


addon = xbmcaddon.Addon()
addon_dir = xbmcvfs.translatePath(addon.getAddonInfo('path'))

_menu = []


class ScanException(Exception):
    pass


def find_scanner() -> None:

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
                                      icon=f"{addon_dir}resources/icon.png")
    else:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32003),
                                      message=addon.getLocalizedString(
                                          32004) % i,
                                      icon=f"{addon_dir}resources/icon.png")


def find_printer() -> None:

    p1 = subprocess.Popen(["lpstat", "-e"],
                          stdout=subprocess.PIPE)
    out, err = p1.communicate()

    i = 0
    for printer in out.decode("utf-8").split("\n"):
        addon.setSetting("printer_%i" % (i + 1), printer)
        i += 1

    p1.stdout.close()

    for j in range(i, 5):
        addon.setSetting("printer_%i" % (j + 1), "")

    if i == 0:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32005),
                                      message=addon.getLocalizedString(32006),
                                      icon=f"{addon_dir}resources/icon.png")
    else:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32007),
                                      message=addon.getLocalizedString(
                                          32008) % (i - 1),
                                      icon=f"{addon_dir}resources/icon.png")


def _get_scanner() -> 'list[str]':

    scanner = addon.getSettingInt("scanner_scanner")

    if scanner == 2:
        return None
    else:
        return addon.getSetting("scanner_%i" % scanner).split("|")


def _get_printer() -> str:

    printer = addon.getSettingInt("output_printer")
    return addon.getSetting("printer_%i" % printer) if printer else ""


def _get_format() -> str:

    return _SCANNER_FORMAT[addon.getSettingInt("scanner_format")]


def _build_dir_structure(path: str):

    def _build_root() -> 'list[dict]':

        tmp_files = _get_tmp_files()

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

        if len(tmp_files) > 0:
            entries += [
                {
                    "path": "/",
                    "name": addon.getLocalizedString(32014),
                    "icon": "icon_pdf",
                    "exec": ["pdf"],
                    "msg": addon.getLocalizedString(32015),
                    "node": []
                }
            ]

        if len(tmp_files) > 0 and addon.getSetting("output_email") == "true":
            entries += [
                {
                    "path": "/",
                    "name": addon.getLocalizedString(32016),
                    "icon": "icon_email",
                    "exec": ["email"],
                    "msg": addon.getLocalizedString(32017),
                    "node": []
                }
            ]

        if len(tmp_files) > 0 and addon.getSettingInt("output_printer") != 0:
            entries += [
                {
                    "path": "/",
                    "name": addon.getLocalizedString(32018) % _get_printer(),
                    "icon": "icon_print",
                    "exec": ["print"],
                    "msg": addon.getLocalizedString(32019) % _get_printer(),
                    "node": []
                }
            ]

        i = 0
        for f in tmp_files:
            i += 1
            entries += [
                {
                    "path": f"/{f}",
                    "name": addon.getLocalizedString(32020) % i,
                    "image": os.path.join(tempfile.gettempdir(), f),
                    "exec": ["preview"]
                }
            ]

        if len(tmp_files) > 0:
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
                    "icon": "icon_archive",
                    "name": addon.getLocalizedString(32025),
                    "node": []
                }
            ]

        return entries

    def _build_archive() -> 'list[dict]':

        _clean_preview()

        pdf_files = _get_pdf_files()

        if addon.getSetting("archive_operations") == "false":
            contextItems = []
        else:
            contextItems = [
                (addon.getLocalizedString(32010), "rename"),
                (addon.getLocalizedString(32011), "delete")
            ]

        pdf_entries = []
        for filename in pdf_files:
            pdf_entries += [
                {
                    "path": filename,
                    "name": filename,
                    "contextItems": contextItems,
                    "node": [],
                    "date": datetime.datetime.fromtimestamp(os.path.getmtime(filename=os.path.join(addon.getSetting("output_folder"), filename))),
                    "file": True
                }
            ]

        entries = [
            {
                "path": "archive",
                "name": addon.getLocalizedString(32025),
                "node": pdf_entries
            }
        ]

        return entries

    def _build_pdf_preview(filename: str) -> 'list[dict]':

        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32000),
                                      message=addon.getLocalizedString(32009),
                                      icon=f"{addon_dir}resources/icon.png")

        _clean_preview()

        _convert_for_preview(filename)

        preview_entries = []
        i = 0
        for f in _get_preview_files():
            i += 1
            preview_entries += [
                {
                    "path": f"/{f}",
                    "name": addon.getLocalizedString(32026) % i,
                    "image": os.path.join(tempfile.gettempdir(), f),
                    "exec": ["preview"]
                }
            ]

        entries = [
            {
                "path": "archive",
                "name": addon.getLocalizedString(32025),
                "node": preview_entries
            }
        ]

        return entries

    global _menu

    splitted_path = path.split("/")
    splitted_path.pop(0)

    entries = []

    if path == "/":
        entries = _build_root()

    elif path == "/archive":
        entries = _build_archive()

    elif path.startswith("/archive") and len(splitted_path) == 2:
        entries = _build_pdf_preview(splitted_path[1])

    _menu = [
        {
            "path": "",
            "node": entries
        }
    ]


def _get_directory_by_path(path: str) -> str:

    if path == "/":
        return _menu[0]

    tokens = path.split("/")[1:]
    directory = _menu[0]

    while len(tokens) > 0:
        path = tokens.pop(0)
        for node in directory["node"]:
            if node["path"] == path:
                directory = node
                break

    return directory


def browse(path: str) -> None:

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

        xbmcplugin.addDirectoryItem(handle=addon_handle,
                                    listitem=li,
                                    url="plugin://" + addon.getAddonInfo("id")
                                    + item_path
                                    + param_string,
                                    isFolder=is_folder)

        return sort_methods

    try:
        _build_dir_structure(path)

        sort_methods = {}
        directory = _get_directory_by_path(path)
        for entry in directory["node"]:
            sort_methods = _add_list_item(entry, path)

        for sort_method in sort_methods:
            xbmcplugin.addSortMethod(addon_handle, sort_method)

        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

    except ScanException:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32027),
                                      message=addon.getLocalizedString(32028),
                                      icon=f"{addon_dir}resources/icon.png")


def _get_tmp_files() -> 'list[str]':
    return _get_files(tempfile.gettempdir(), "^" + _IMG_FILE)


def _get_pdf_files() -> 'list[str]':
    return _get_files(addon.getSetting("output_folder"), "^.+\.pdf$")


def _get_preview_files() -> 'list[str]':
    return _get_files(tempfile.gettempdir(), "^" + _PDF_PREVIEW_FILE)


def _get_files(dir: str, pattern: str) -> 'list[str]':

    p = re.compile(pattern, re.IGNORECASE)
    files = os.listdir(dir)
    result = []
    for s in files:
        m = p.match(s)
        if m:
            result += [s]

    result.sort()

    return result


def _scan():

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
                            f"{_IMG_FILE}.{time.time()}.{_get_format()}")
    _file = open(tmp_file, "w")

    p = subprocess.Popen(call, stdout=_file, stderr=subprocess.PIPE)
    p.wait()
    _file.close()

    if addon.getSettingInt("scanner_mode") == 2:
        _convert_to_monochrome(tmp_file)


def _pdf():

    tmp_files = _get_tmp_files()
    full_path = []
    for f in tmp_files:
        full_path += [os.path.join(tempfile.gettempdir(), f)]

    pdf_file = "%s.scan.pdf" % datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    call = ["convert"]
    call += full_path
    call += [os.path.join(tempfile.gettempdir(), pdf_file)]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()

    return pdf_file


def _convert_to_monochrome(input_file):

    call = ["convert",
            "-monochrome",
            input_file,
            input_file
            ]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()


def _convert_for_preview(input_file):

    call = ["convert",
            "-density", _ARCHIVE_RESOLUTIONS[
                addon.getSettingInt("archive_resolution")],
            "-quality", "90",
            "-background", "white", "-alpha", "background", "-alpha", "off",
            "%s%s" % (addon.getSetting("output_folder"), input_file),
            os.path.join(tempfile.gettempdir(),
                         f"{_PDF_PREVIEW_FILE}.{input_file}.png")
            ]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()


def _ocr(pdf_file):

    pdf_file = os.path.join(tempfile.gettempdir(), pdf_file)
    ocr_file = f"{pdf_file}.ocr"

    call = [os.path.join(addon_dir, "resources", "lib", "ocrmypdf_wrapper"),
            pdf_file,
            ocr_file]

    p = subprocess.Popen(call, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    p.stdout.close()

    os.remove(pdf_file)
    shutil.move(ocr_file, pdf_file)


def _rename_pdf(path):

    splitted_path = path.split("/")
    filename = splitted_path[-1]

    renamed_file = xbmcgui.Dialog().input(addon.getLocalizedString(32079),
                                          filename,
                                          xbmcgui.INPUT_ALPHANUM)

    if renamed_file != "":
        archive = addon.getSetting("output_folder")
        shutil.move(f"{archive}{filename}",
                    f"{archive}{renamed_file}")


def _delete_pdf(path):

    splitted_path = path.split("/")
    file_to_delete = splitted_path[-1]

    ret = xbmcgui.Dialog().yesno(addon.getLocalizedString(
        32000), addon.getLocalizedString(32080) % file_to_delete)
    if ret:
        os.remove("%s%s" % (addon.getSetting("output_folder"),
                            file_to_delete))


def _lampoff():

    call = ["scanimage",
            "-n", "--lamp-switch=no"]

    _scanner = _get_scanner()
    if _scanner != None and len(_scanner) == 2:
        call += [f"--device-name={_scanner[1]}"]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()


def _get_email_address() -> str:

    addressbook = [a for a in addon.getSetting(
        "output_emailaddress").split("|") if a.strip()]
    selection = 0
    if addressbook and addressbook[0] != "":
        selection = xbmcgui.Dialog().select(
            heading=addon.getLocalizedString(32076), list=addressbook + [addon.getLocalizedString(32077)], preselect=0)

    if selection == -1:
        return None

    if selection == len(addressbook) or not addressbook or addressbook[0] == "":
        recipient = xbmcgui.Dialog().input(addon.getLocalizedString(32030))
        recipient = recipient.strip()
        match = re.match(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}$", recipient)
        if not match:
            xbmcgui.Dialog().ok(heading=addon.getLocalizedString(
                32000), message=addon.getLocalizedString(32078))
            return None
    else:
        recipient = addressbook[selection]

    if recipient in addressbook:
        addressbook.remove(recipient)
    addressbook.insert(0, recipient)
    addon.setSetting("output_emailaddress", "|".join(addressbook))

    return recipient


def _email(pdf_file: str, recipient: str) -> None:

    call = ["mail",
            "-A", "%s%s" % (addon.getSetting("output_folder"),
                            pdf_file),
            "-s", f"{addon.getLocalizedString(32000)}: {pdf_file}",
            recipient
            ]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()


def _print(pdf_file):

    call = ["lp",
            "-t", f"{addon.getLocalizedString(32000)}: {pdf_file}",
            ]

    if _get_printer() != "":
        call += ["-d", _get_printer()]

    call += ["%s%s" % (addon.getSetting("output_folder"),  pdf_file)]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()


def _undo():

    tmp_files = _get_tmp_files()
    os.remove(os.path.join(tempfile.gettempdir(), tmp_files[-1]))


def _clean():

    tmp_files = _get_tmp_files()
    for f in tmp_files:
        os.remove(os.path.join(tempfile.gettempdir(), f))


def _clean_preview():

    for f in _get_preview_files():
        os.remove(os.path.join(tempfile.gettempdir(), f))


def _preview(path):

    tokens = path.split("/")[1:]
    url = os.path.join(tempfile.gettempdir(), tokens[-1])
    xbmc.executebuiltin(f"ShowPicture({url})")


def execute(path, params):

    if "silent" not in params and "msg" in params:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32000),
                                      message=params["msg"][0], icon=f"{addon_dir}resources/icon.png")

    try:
        if params["exec"][0] == "scan":
            _scan()

        elif params["exec"][0] == "undo":
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno(heading=addon.getLocalizedString(32000),
                               message=addon.getLocalizedString(32029))
            if ret:
                _undo()
                if len(_get_tmp_files()) == 0:
                    _lampoff()

        if params["exec"][0] == "preview":
            _preview(path)

        if params["exec"][0] == "email":
            recipient = _get_email_address()
            if not recipient:
                return

        if params["exec"][0] in ["pdf", "email", "print"]:

            _lampoff()
            pdf_file = _pdf()
            _clean()

            if addon.getSetting("output_ocr") == "true":
                _ocr(pdf_file)

            shutil.move(os.path.join(tempfile.gettempdir(), pdf_file),
                        "%s%s" % (addon.getSetting("output_folder"),
                                  pdf_file))

        if params["exec"][0] == "email":
            _email(pdf_file, recipient)

        if params["exec"][0] == "print":
            _print(pdf_file)

        if params["exec"][0] in ["clean"]:
            ret = xbmcgui.Dialog().yesno(heading=addon.getLocalizedString(32000),
                                         message=addon.getLocalizedString(32031))
            if ret:
                _clean()
                _lampoff()

        if params["exec"][0] == "rename":
            _rename_pdf(path)

        elif params["exec"][0] == "delete":
            _delete_pdf(path)

        if params["exec"][0] in ["rename", "delete"]:
            xbmc.executebuiltin('Container.Update("plugin://%s%s","update")'
                                % (addon.getAddonInfo("id"), "/archive"))

        if "silent" not in params and "msg" in params:
            xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32032),
                                          message=params["msg"][0], icon=f"{addon_dir}resources/icon.png")

            xbmc.executebuiltin('Container.Update("plugin://%s","update")'
                                % addon.getAddonInfo("id"))

    except ScanException:
        if "silent" not in params:
            xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32027),
                                          message=params["msg"][0], icon=f"{addon_dir}resources/icon.png")


if __name__ == '__main__':

    if sys.argv[1] == "find_scanner":
        find_scanner()

    elif sys.argv[1] == "find_printer":
        find_printer()

    else:
        addon_handle = int(sys.argv[1])
        path = urllib.parse.urlparse(sys.argv[0]).path
        url_params = urllib.parse.parse_qs(sys.argv[2][1:])

        if "exec" in url_params:
            execute(path, url_params)

        else:
            browse(path)
