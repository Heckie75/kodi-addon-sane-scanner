import os
import shutil
import tempfile

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from resources.lib import archive, email, pdf, preview, printer, scanner


def execute(url, params):

    addon = xbmcaddon.Addon()
    addon_dir = xbmcvfs.translatePath(addon.getAddonInfo('path'))

    if "msg" in params:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32000),
                                      message=params["msg"][0], icon=f"{addon_dir}resources/assets/icon.png")

    try:
        if params["exec"][0] == "scan":
            scanner.scan()

        elif params["exec"][0] in ["scan2pdf", "scan2email", "scan2print"]:

            scanner.lampoff()
            if params["exec"][0] == "scan2email":
                recipients = email.ask_email_addresses()
                if not recipients:
                    return

            pdf_file = pdf.convert_to_pdf(scanner.get_scanned_files())
            scanner.delete_scanned_files()

            if addon.getSetting("output_ocr") == "true":
                pdf.add_ocr_layer(pdf_file)

            current_file = pdf_file
            pdf_file = xbmcgui.Dialog().input(addon.getLocalizedString(32010),
                                              pdf_file,
                                              xbmcgui.INPUT_ALPHANUM)

            pdf_file = pdf_file or current_file
            if not pdf_file.lower().endswith(".pdf"):
                pdf_file += ".pdf"

            shutil.move(os.path.join(tempfile.gettempdir(), current_file),
                        os.path.join(addon.getSetting("output_folder"), pdf_file))

            if params["exec"][0] == "scan2email":
                email.send_email(addon.getSetting(
                    "output_folder"), pdf_file, recipients)

            elif params["exec"][0] == "scan2print":
                printer.print_(addon.getSetting("output_folder"), pdf_file)

        elif params["exec"][0] == "preview":
            preview.preview(url)

        elif params["exec"][0] == "play":
            fullpath, _, _ = archive.get_real_path_in_archive(url)
            xbmc.executebuiltin(f"PlayMedia({fullpath})")

        elif params["exec"][0] == "show":
            fullpath, _, _ = archive.get_real_path_in_archive(url)
            xbmc.executebuiltin(f"ShowPicture({fullpath})")

        elif params["exec"][0] == "undo":
            dialog = xbmcgui.Dialog()
            yes = dialog.yesno(heading=addon.getLocalizedString(32000),
                               message=addon.getLocalizedString(32029))
            if yes:
                scanner.delete_latest_scanned_file()
                if not scanner.get_scanned_files():
                    scanner.lampoff()

        elif params["exec"][0] in ["clean"]:
            yes = xbmcgui.Dialog().yesno(heading=addon.getLocalizedString(32000),
                                         message=addon.getLocalizedString(32031))
            if yes:
                scanner.delete_scanned_files()
                scanner.lampoff()

        elif params["exec"][0] == "email":
            recipients = email.ask_email_addresses()
            if recipients:
                _, folder, filename = archive.get_real_path_in_archive(url)
                email.send_email(folder, filename, recipients)

        elif params["exec"][0] == "print":
            _, folder, pdf_file = archive.get_real_path_in_archive(url)
            printer.print_(folder, pdf_file)

        if params["exec"][0] in ["rename", "delete", "move", "mkdir"]:

            refresh = None
            if params["exec"][0] == "rename":
                refresh = archive.rename(url)

            elif params["exec"][0] == "delete":
                refresh = archive.delete(url)

            elif params["exec"][0] == "move":
                refresh = archive.move(url)

            elif params["exec"][0] == "mkdir":
                refresh = archive.mkdir(url)

            if refresh:
                xbmc.executebuiltin('Container.Update("plugin://%s%s","update")'
                                    % (addon.getAddonInfo("id"), refresh))

        elif params["exec"][0] in ["scan", "undo", "clean", "scan2pdf", "scan2email", "scan2print"]:
            xbmc.executebuiltin('Container.Update("plugin://%s","update")'
                                % addon.getAddonInfo("id"))

        if "msg" in params:
            xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32032),
                                          message=params["msg"][0], icon=f"{addon_dir}resources/assets/icon.png")

    except Exception:
        xbmcgui.Dialog().notification(heading=addon.getLocalizedString(32027),
                                      message=params["msg"][0], icon=f"{addon_dir}resources/assets/icon.png")
