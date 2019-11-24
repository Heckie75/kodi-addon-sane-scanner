#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import os
import re
import shutil
import subprocess
import sys
import time
import urlparse

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

__PLUGIN_ID__     = "plugin.picture.sane-scanner"
_PLUGIN_NAME      = "Kodi Sane Scanner"

_TMP_FOLDER       = "/tmp/"
_IMG_FILE         = "kodi-sane-scanner-img"
_PDF_PREVIEW_FILE = "kodi-sane-scanner-pdf"

_SCANNER_MODES = [
            [ "--mode", "Lineart" ],
            [ "--mode", "Gray" ],
            [ "--mode", "Color" ]
        ]

_SCANNNER_RESOLUTIONS = [
            [ "--resolution", "150" ],
            [ "--resolution", "200" ],
            [ "--resolution", "300" ],
            [ "--resolution", "600" ]
        ]

_ARCHIVE_RESOLUTIONS = [
            "150",
            "200",
            "300",
            "600"
        ]

_SCANNER_DIMENSIONS = [
            [],
            [ "-l", "0", "-t", "0", "-x", "216mm", "-y", "279mm" ],
            [ "-l", "0", "-t", "0", "-x", "210mm", "-y", "297mm" ],
            [ "-l", "0", "-t", "0", "-x", "148mm", "-y", "210mm" ],
            [ "-l", "0", "-t", "0", "-x", "105mm", "-y", "148mm" ],
        ]

_SCANNER_FORMAT = [
    "png",
    "jpeg"
]




reload(sys)
sys.setdefaultencoding('utf8')

settings = xbmcaddon.Addon(id=__PLUGIN_ID__);
addon_dir = xbmc.translatePath( settings.getAddonInfo('path') )

_menu = []




class ScanException(Exception):
    pass




def find_scanner():

    p1 = subprocess.Popen(["scanimage", "-f" "%d %v %m %t%n"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    out, err = p1.communicate()
    xbmc.log(out, xbmc.LOGNOTICE)

    i = 0
    for match in re.finditer('([^ ]+) (.+)', out.decode("utf-8")):
        settings.setSetting("scanner_%i" % i, "%s|%s" %
                (match.group(2), match.group(1)))
        i = i + 1

    p1.stdout.close()

    for j in range(i, 2):
        settings.setSetting("scanner_%i" % j, "")

    if i == 0:
        xbmc.executebuiltin(
            "Notification(No scanner found, "
            "Check if scanner is connected!)")
    else:
        xbmc.executebuiltin(
            "Notification(Scanners found, "
            "%i scanners added to device list)" % i)




def find_printer():

    p1 = subprocess.Popen(["lpstat", "-e"],
                                stdout=subprocess.PIPE)
    out, err = p1.communicate()
    xbmc.log(out, xbmc.LOGNOTICE)

    i = 0
    for printer in out.decode("utf-8").split("\n"):

        settings.setSetting("printer_%i" % (i + 1), "%s"
                % printer)
        i = i + 1

    p1.stdout.close()

    for j in range(i, 5):
        settings.setSetting("printer_%i" % (j + 1), "")

    if i == 0:
        xbmc.executebuiltin(
            "Notification(No printer found, "
            "Check if printer is connected!)")
    else:
        xbmc.executebuiltin(
            "Notification(Printers found, "
            "%i printers added to device list)" % i)




def _get_scanner():

    scanner = settings.getSetting("scanner_scanner")
    return settings.getSetting("scanner_%s" % scanner).split("|")




def _get_printer():

    printer = settings.getSetting("output_printer")
    if printer != "0":
        return settings.getSetting("printer_%s" % printer)
    else:
        return ""




def _get_format():

    return _SCANNER_FORMAT[int(settings.getSetting("scanner_format"))]




def _build_param_string(param, values, current = ""):

    if values == None:
        return current

    for v in values:
        current += "?" if len(current) == 0 else "&"
        current += param + "=" + str(v)

    return current




def _add_list_item(entry, path):

    if path == "/":
        path = ""

    item_path = path + "/" + entry["path"]
    item_id = item_path.replace("/", "_")

    param_string = ""
    if "exec" in entry:
        param_string = _build_param_string(
            param = "exec",
            values = entry["exec"],
            current = param_string)

    if "param" in entry:
        param_string = _build_param_string(
            param = entry["param"][0],
            values = [ entry["param"][1] ],
            current = param_string)

    if "msg" in entry:
        param_string = _build_param_string(
            param = "msg",
            values = [ entry["msg"] ],
            current = param_string)

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

    li = xbmcgui.ListItem(label, iconImage=icon_file)

    if "image" in entry:
        li.setAvailableFanart([
                    {"image": icon_file, "preview": icon_file}
                ])

    if "contextItems" in entry:
        commands = []
        for ci in entry["contextItems"]:
            p = _build_param_string(
                                    param = "exec",
                                    values = [ ci[1] ],
                                    current = "")
            url = "plugin://%s%s%s" % (__PLUGIN_ID__, item_path, p)
            commands.append(( ci[0], 'XBMC.RunPlugin(%s)' % url, ))

        li.addContextMenuItems(commands)


    xbmcplugin.addDirectoryItem(handle=addon_handle,
                            listitem=li,
                            url="plugin://" + __PLUGIN_ID__
                            + item_path
                            + param_string,
                            isFolder=is_folder)




def  _build_pdf_preview(filename):

    xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                    % (_PLUGIN_NAME, "Rendering preview... be patient!", addon_dir))

    _clean_preview()

    _convert_for_preview(filename)

    preview_entries = []
    i = 0
    for f in _get_preview_files():
        xbmc.log(filename, xbmc.LOGNOTICE)
        i = i + 1
        preview_entries += [
            {
                "path" : "/%s" % f,
                "name" : "Page %i" % i,
                "image" : "%s%s" % (_TMP_FOLDER, f),
                "exec" : [ "preview" ]
            }
        ]

    entries = [
        {
        "path" : "archive",
        "name" : "Archive",
        "node" : preview_entries
        }
    ]

    return entries




def  _build_archive():

    _clean_preview()

    pdf_files = _get_pdf_files()

    pdf_entries = []
    for filename in pdf_files:
        pdf_entries += [
            {
            "path" : filename,
            "name" : filename,
            "contextItems" : [
                ('Rename PDF file', 'rename')
            ],
            "node" : []
            }
        ]


    entries = [
        {
        "path" : "archive",
        "name" : "Archive",
        "node" : pdf_entries
        }
    ]

    return entries




def _build_root():

    tmp_files = _get_tmp_files()

    entries = [
        {
            "path" : "/",
            "name" : "scan image",
            "icon" : "icon_scan",
            "exec" : [ "scan" ],
            "msg" : "Scanning page... be patient!",
            "node" : []
        }
    ]

    if len(tmp_files) > 0:
        entries += [
            {
                "path" : "/",
                "name" : "create PDF",
                "icon" : "icon_pdf",
                "exec" : [ "pdf" ],
                "msg" : "Creating PDF file",
                "node" : []
            }
        ]

    if len(tmp_files) > 0 and settings.getSetting("output_email") == "1":
        entries += [
            {
                "path" : "/",
                "name" : "create PDF and send email to %s" % settings.getSetting("output_emailaddress"),
                "icon" : "icon_email",
                "exec" : [ "email" ],
                "msg" : "Sending to %s" % settings.getSetting("output_emailaddress"),
                "node" : []
            }
        ]

    if len(tmp_files) > 0 and settings.getSetting("output_printer") != "0":
        entries += [
            {
                "path" : "/",
                "name" : "create PDF and print on %s" % _get_printer(),
                "icon" : "icon_print",
                "exec" : [ "print" ],
                "msg" : "Printing on %s" % _get_printer(),
                "node" : []
            }
        ]

    i = 0
    for f in tmp_files:
        i = i + 1
        entries += [
            {
                "path" : "/%s" % f,
                "name" : "preview page %i" % i,
                "image" : "%s%s" % (_TMP_FOLDER, f),
                "exec" : [ "preview" ]
            }
        ]

    if len(tmp_files) > 0:
        entries += [
            {
                "path" : "/",
                "name" : "remove latest page",
                "icon" : "icon_undo",
                "exec" : [ "undo" ],
                "msg" : "removing latest page",
                "node" : []
            },
            {
                "path" : "/",
                "name" : "clean whole filing",
                "icon" : "icon_trash",
                "exec" : [ "clean" ],
                "msg" : "Cleaning all pages",
                "node" : []
            }
        ]

    if settings.getSetting("archive") == "true":
        entries += [
            {
            "path" : "archive",
            "name" : "Archive",
            "node" : []
            }
        ]

    return entries




def _build_dir_structure(path, url_params):

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
        "path" : "",
        "node" : entries
        }
    ]




def _get_directory_by_path(path):

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




def browse(path, url_params):

    try:
        entries = _build_dir_structure(path, url_params)

        directory = _get_directory_by_path(path)
        for entry in directory["node"]:
            _add_list_item(entry, path)

        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

    except ScanException:
        xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % ("Execution failed!",
                           "Try again!", addon_dir))




def _get_tmp_files():
    return _get_files(_TMP_FOLDER, "^" + _IMG_FILE)




def _get_pdf_files():
    return _get_files(settings.getSetting("output_folder"), "^.+\.pdf$")




def _get_preview_files():
    return _get_files(_TMP_FOLDER, "^" + _PDF_PREVIEW_FILE)




def _get_files(dir, pattern):

    p = re.compile(pattern, re.IGNORECASE)
    files = os.listdir(dir)
    result = []
    for s in files:
        m = p.match(s)
        if m:
            result += [ s ]

    result.sort()

    return result




def _scan():

    call = ["scanimage",
            "--format=%s" % _get_format(),
            "--brightness", settings.getSetting("scanner_brightness"),
            "--contrast", settings.getSetting("scanner_contrast")
        ]

    if len(_get_scanner()) == 2:
        call += [ "--device-name=%s" % _get_scanner()[1] ]

    call += _SCANNER_DIMENSIONS[
                int(settings.getSetting("scanner_dimension"))]
    call += _SCANNER_MODES[
                int(settings.getSetting("scanner_mode"))]
    call += _SCANNNER_RESOLUTIONS[
                int(settings.getSetting("scanner_resolution"))]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    tmp_file = open("%s%s.%i.%s" % (_TMP_FOLDER, _IMG_FILE,
                                    time.time(),
                                    _get_format()),
                "w")
    p = subprocess.Popen(call, stdout=tmp_file)
    p.wait()
    tmp_file.close()




def _pdf():

    tmp_files = _get_tmp_files()
    full_path = []
    for f in tmp_files:
        full_path += [ "%s%s" % (_TMP_FOLDER, f) ]

    pdf_file = "%s.scan.pdf" % datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    call = ["convert"]
    call += full_path
    call += [ "%s%s" % (_TMP_FOLDER, pdf_file) ]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()

    return pdf_file




def _convert_for_preview(input_file):

    call = ["convert",
            "-density", _ARCHIVE_RESOLUTIONS[
                int(settings.getSetting("archive_resolution"))],
            "-quality", "90",
            "-background", "white", "-alpha", "background", "-alpha", "off",
            "%s%s" % (settings.getSetting("output_folder"), input_file),
            "%s%s.%s%s" % (_TMP_FOLDER, _PDF_PREVIEW_FILE, input_file, ".png")
        ]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()




def _ocr(pdf_file):

    pdf_file = "%s%s" % (_TMP_FOLDER, pdf_file)
    ocr_file = "%s.ocr" % pdf_file

    call = [ addon_dir + os.sep + "resources"
                + os.sep + "lib"
                + os.sep + "ocrmypdf_wrapper",
            pdf_file,
            ocr_file ]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)
    p = subprocess.Popen(call, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
    out, err = p.communicate()
    p.stdout.close()

    xbmc.log(out, xbmc.LOGNOTICE)
    xbmc.log(err, xbmc.LOGNOTICE)

    os.remove(pdf_file)
    shutil.move(ocr_file, pdf_file)




def _rename_pdf(path):
    
    splitted_path = path.split("/")
    filename = splitted_path[-1]

    renamed_file = xbmcgui.Dialog().input("Rename PDF file", 
                                        filename, 
                                        xbmcgui.INPUT_ALPHANUM)
    
    if renamed_file != "":
        archive = settings.getSetting("output_folder")
        shutil.move("%s%s" % (archive, filename), 
                    "%s%s" % (archive, renamed_file))




def _lampoff():

    call = [ "scanimage",
            "-n", "--lamp-switch=no" ]

    if len(_get_scanner()) == 2:
        call += [ "--device-name=%s" % _get_scanner()[1] ]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()




def _email(pdf_file):

    call = [ "mail",
            "-A", "%s%s" % (settings.getSetting("output_folder"),
                            pdf_file),
            "-s", "%s: %s" % (_PLUGIN_NAME, pdf_file),
            settings.getSetting("output_emailaddress")
            ]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()




def _print(pdf_file):

    call = [ "lp",
            "-t", "%s: %s" % (_PLUGIN_NAME, pdf_file),
            ]

    if _get_printer() != "":
        call += [ "-d", _get_printer() ]

    call += [ "%s%s" % (settings.getSetting("output_folder"),  pdf_file) ]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()




def _undo():

    tmp_files = _get_tmp_files()
    os.remove("%s%s" % (_TMP_FOLDER, tmp_files[-1]))




def _clean():

    tmp_files = _get_tmp_files()
    for f in tmp_files:
        os.remove("%s%s" % (_TMP_FOLDER, f))




def _clean_preview():

    for f in _get_preview_files():
        os.remove("%s%s" % (_TMP_FOLDER, f))




def _preview(path):

    tokens = path.split("/")[1:]
    url = "%s%s" % (_TMP_FOLDER, tokens[-1])
    xbmc.log(url, xbmc.LOGNOTICE)
    xbmc.executebuiltin('ShowPicture(%s)' % url)




def execute(path, params):

    if "silent" not in params and "msg" in params:
        xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % (_PLUGIN_NAME, params["msg"][0], addon_dir))

    try:
        xbmc.log(path, xbmc.LOGNOTICE)
        xbmc.log(" ".join(params["exec"]), xbmc.LOGNOTICE)

        if params["exec"][0] == "scan":
            _scan()

        elif params["exec"][0] == "undo":
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno(_PLUGIN_NAME, "Do you want to remove latest page?")
            if ret:
                _undo()
                if len(_get_tmp_files()) == 0:
                    _lampoff()

        if params["exec"][0] == "preview":
            _preview(path)

        if params["exec"][0] in ["pdf", "email", "print"]:
            _lampoff()
            pdf_file = _pdf()
            _clean()

            if settings.getSetting("output_ocr") == "1":
                 _ocr(pdf_file)

            shutil.move("%s%s" % (_TMP_FOLDER, pdf_file),
                    "%s%s" % (settings.getSetting("output_folder"),
                            pdf_file))

        if params["exec"][0] == "email":
            _email(pdf_file)

        if params["exec"][0] == "print":
            _print(pdf_file)

        if params["exec"][0] in ["clean"]:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno(_PLUGIN_NAME,
                    "Do you want to clean filing?")
            if ret:
                _clean()
                _lampoff()

        if params["exec"][0] == "rename":
            _rename_pdf(path)
            xbmc.executebuiltin('Container.Update("plugin://%s%s","update")' 
                        % (__PLUGIN_ID__, "/archive"))               

        if "silent" not in params and "msg" in params:
            xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % ("Success!", params["msg"][0], addon_dir))

            xbmc.executebuiltin('Container.Update("plugin://%s%s","update")' 
                        % __PLUGIN_ID__)

    except ScanException:
        if "silent" not in params:
            xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % ("Failed! Try again", params["msg"][0], addon_dir))




if __name__ == '__main__':

    if sys.argv[1] == "find_scanner":
        find_scanner()
    elif sys.argv[1] == "find_printer":
        find_printer()
    else:
        addon_handle = int(sys.argv[1])
        path = urlparse.urlparse(sys.argv[0]).path
        url_params = urlparse.parse_qs(sys.argv[2][1:])

        if "exec" in url_params:
            execute(path, url_params)

        else:
            browse(path, url_params)