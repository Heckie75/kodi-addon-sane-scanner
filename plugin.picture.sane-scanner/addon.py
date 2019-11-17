#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import json
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

__PLUGIN_ID__ = "plugin.picture.sane-scanner"

_TMP_FOLDER = "/tmp/"
_TMP_FILE = "kodi-sane-scanner"

_SCANNER_MODES = [
            [ "--mode", "Lineart" ], 
            [ "--mode", "Greyscale" ], 
            [ "--mode", "Color" ]
        ]

_SCANNNER_RESOLUTIONS = [ 
            [ "--resolution", "150" ], 
            [ "--resolution", "200" ], 
            [ "--resolution", "300" ], 
            [ "--resolution", "600" ]
        ]

_SCANNER_DIMENSIONS = [
            [],
            [ "-l", "0", "-t", "0", "-x", "216mm", "-y", "279mm" ], 
            [ "-l", "0", "-t", "0", "-x", "210mm", "-y", "297mm" ],
            [ "-l", "0", "-t", "0", "-x", "148mm", "-y", "210mm" ],
            [ "-l", "0", "-t", "0", "-x", "105mm", "-y", "148mm" ],
        ]


reload(sys)
sys.setdefaultencoding('utf8')

settings = xbmcaddon.Addon(id=__PLUGIN_ID__);
addon_dir = xbmc.translatePath( settings.getAddonInfo('path') )

_menu = []




class ContinueLoop(Exception):
    pass




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
        settings.setSetting("scanner_%i" % i, "%s|%s" % (match.group(1), match.group(2)))
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

    p1 = subprocess.Popen(["lpstat", "-a"],
                                stdout=subprocess.PIPE)
    out, err = p1.communicate()
    xbmc.log(out, xbmc.LOGNOTICE)

    i = 0
    for match in re.finditer('([^ ]+) .+', out.decode("utf-8")):

        settings.setSetting("printer_%i" % (i + 1), "%s" % (match.group(1)))
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




def _get_printer():

    printer = settings.getSetting("output_printer")
    if printer != "0":
        return settings.getSetting("printer_%s" % printer)
    else:
        return ""




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

    is_folder = "node" in entry and entry["node"]

    label = entry["name"]

    if "image" in entry:
        icon_file = entry["image"]
    elif "icon" in entry:
        icon_file = os.path.join(addon_dir, "resources", "assets", entry["icon"] + ".png")
    else:
        icon_file = None

    li = xbmcgui.ListItem(label, iconImage=icon_file)

    if "image" in entry:
        li.setAvailableFanart([{"image": icon_file, "preview": icon_file}])

    xbmcplugin.addDirectoryItem(handle=addon_handle,
                            listitem=li,
                            url="plugin://" + __PLUGIN_ID__
                            + item_path
                            + param_string,
                            isFolder=is_folder)





def _build_dir_structure(path, url_params):

    global _menu

    tmp_files = _get_tmp_files()

    entries = [
        {
            "path" : "/",
            "name" : "scan image",
            "icon" : "icon_scan",
            "exec" : [ "scan" ],
            "msg" : "Scanning page... be patient!",
            "node" : True
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
                "node" : True
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
                "node" : True
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
                "node" : True
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
                "exec" : [ "preview" ],
                "node" : False
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
                "node" : True
            },
            {
                "path" : "/",
                "name" : "clean whole filing",
                "icon" : "icon_trash",
                "exec" : [ "clean" ],
                "msg" : "Cleaning all pages",
                "node" : True
            }            
        ]

    return entries




def browse(path, url_params):

    try:
        entries = _build_dir_structure(path, url_params)

        for entry in entries:
            _add_list_item(entry, path)

        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

    except ScanException:
        xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % ("Execution failed!",
                           "Try again!", addon_dir))




def _get_tmp_files():

    files = os.listdir(_TMP_FOLDER)
    result = []
    for s in files:
        if s.startswith(_TMP_FILE):
            result += [ s ]
    
    result.sort()

    return result




def _scan():

    call = ["scanimage", 
            "--format=png",
            "--brightness", settings.getSetting("scanner_brightness")
        ] 

    call += _SCANNER_DIMENSIONS[int(settings.getSetting("scanner_dimension"))]
    call += _SCANNER_MODES[int(settings.getSetting("scanner_mode"))]
    call += _SCANNNER_RESOLUTIONS[int(settings.getSetting("scanner_resolution"))]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    tmp_file = open("%s%s.%i.png" % (_TMP_FOLDER, _TMP_FILE, time.time()), "w")
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




def _ocr(pdf_file):

    pdf_file = "%s%s" % (_TMP_FOLDER, pdf_file)
    ocr_file = "%s.ocr" % pdf_file

    call = [ "ocrmypdf", "-l", "deu",
            pdf_file,
            ocr_file ]

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    p = subprocess.Popen(call, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    p.stdout.close()

    xbmc.log(out, xbmc.LOGNOTICE)
    xbmc.log(err, xbmc.LOGNOTICE)

    os.remove(pdf_file)
    shutil.move(ocr_file, pdf_file)




def _lampoff():

    call = [ "scanimage", "-n", "--lamp-switch=no" ] 

    xbmc.log(" ".join(call), xbmc.LOGNOTICE)

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()




def _email(pdf_file):
    pass
#   mail -A "${PDF_FOLDER}${TARGET_FILE}" -s "Kodi Sane Scanner: ${TARGET_FILE}" email@web.de




def _print(pdf_file):
    pass
#  lp "${PDF_FOLDER}${TARGET_FILE}"




def _undo():
    
    tmp_files = _get_tmp_files()
    os.remove("%s%s" % (_TMP_FOLDER, tmp_files[-1]))




def _clean():
        
    tmp_files = _get_tmp_files()
    for f in tmp_files:
        os.remove("%s%s" % (_TMP_FOLDER, f))




def _preview(path):

    tokens = path.split("/")[1:]
    url = "%s%s" % (_TMP_FOLDER, tokens[-1])
    xbmc.log(url, xbmc.LOGNOTICE)
    xbmc.executebuiltin('ShowPicture(%s)' % url)





def execute(path, params):

    if "silent" not in params and "msg" in params:
        xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % ("Kodi Sane Scanner", params["msg"][0], addon_dir))

    try:
        xbmc.log(" ".join(params["exec"]), xbmc.LOGNOTICE);

        if params["exec"][0] == "scan":
            _scan()

        elif params["exec"][0] == "undo":
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno("Kodi Sane Scanner", "Do you want to remove latest page?")
            if ret:
                _undo()
        
        if params["exec"][0] == "preview":
            _preview(path)

        if params["exec"][0] in ["pdf", "email", "print"]:
            _lampoff()
            pdf_file = _pdf()
            _clean()

#            if settings.getSetting("output_ocr") == "1":
#                 _ocr(pdf_file)

            shutil.move("%s%s" % (_TMP_FOLDER, pdf_file),
                    "%s%s" % (settings.getSetting("output_folder"), pdf_file))

        if params["exec"][0] == "email":
            _email(pdf_file)

        if params["exec"][0] == "print":
            _print(pdf_file)

        if params["exec"][0] in ["clean"]:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno("Kodi Sane Scanner", "Do you want to clean filing?")
            if ret:
                _clean()

        time.sleep(0.5)

        if "silent" not in params and "msg" in params:
            xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % ("Success!", params["msg"][0], addon_dir))

            xbmc.executebuiltin('Container.Update("plugin://%s","update")' % __PLUGIN_ID__)

    except ScanException:
        if "silent" not in params:
            xbmc.executebuiltin("Notification(%s, %s, %s/icon.png)"
                        % ("Failed! Try again", params["msg"][0], addon_dir))




if __name__ == '__main__':

    if sys.argv[1] == "find_scanner":
        find_scanner()
    if sys.argv[1] == "find_printer":
        find_printer()
    else:
        addon_handle = int(sys.argv[1])
        path = urlparse.urlparse(sys.argv[0]).path
        url_params = urlparse.parse_qs(sys.argv[2][1:])

        if "exec" in url_params:
            execute(path, url_params)

        else:
            browse(path, url_params)