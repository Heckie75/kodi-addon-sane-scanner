import datetime
import os
import subprocess
import tempfile

import xbmcaddon
import xbmcvfs
from resources.lib import fileutils


def convert_to_pdf(scanned_files: 'list[str]') -> str:

    full_path = []
    for f in scanned_files:
        full_path += [os.path.join(tempfile.gettempdir(), f)]

    pdf_file = "%s.scan.pdf" % datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    call = ["convert"]
    call += full_path
    call += [os.path.join(tempfile.gettempdir(), pdf_file)]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()

    return pdf_file


def add_ocr_layer(pdf_file: str) -> None:

    addon = xbmcaddon.Addon()
    addon_dir = xbmcvfs.translatePath(addon.getAddonInfo('path'))

    pdf_file = os.path.join(tempfile.gettempdir(), pdf_file)
    ocr_file = f"{pdf_file}.ocr"

    """
    call = [os.path.join(addon_dir, "resources", "lib", "ocrmypdf_wrapper"),
            pdf_file,
            ocr_file]
    """

    call = ["ocrmypdf", "-l", "deu", fileutils.encode(pdf_file), fileutils.encode(ocr_file)]

    p = subprocess.Popen(call, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    p.stdout.close()

    fileutils.remove(pdf_file)
    fileutils.move(ocr_file, pdf_file)
