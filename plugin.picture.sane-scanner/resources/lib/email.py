import os
import re
import subprocess

import xbmcaddon
import xbmcgui


def ask_email_address() -> str:

    addon = xbmcaddon.Addon()
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


def send_email(folder: str, filename: str, recipient: str) -> None:

    addon = xbmcaddon.Addon()
    call = ["mail",
            "-A", os.path.join(folder, filename),
            "-s", f"{addon.getLocalizedString(32000)}: {filename}",
            recipient
            ]

    p = subprocess.Popen(call, stdout=subprocess.PIPE)
    p.wait()
    p.stdout.close()
