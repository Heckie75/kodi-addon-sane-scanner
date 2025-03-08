import os
import re
import subprocess

import xbmcaddon
import xbmcgui


def ask_email_addresses() -> 'list[str]':

    addon = xbmcaddon.Addon()
    addressbook = [a for a in addon.getSetting(
        "output_emailaddress").split("|") if a.strip()]

    selection = xbmcgui.Dialog().multiselect(
        heading=addon.getLocalizedString(32076), options=addressbook + [addon.getLocalizedString(32077)], preselect=[0])

    if not selection:
        return None

    recipients = list()

    # add new recipient
    if len(addressbook) in selection or not addressbook or addressbook[0] == "":
        recipient = xbmcgui.Dialog().input(addon.getLocalizedString(32030))
        recipient = recipient.strip()
        match = re.match(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}$", recipient)
        if not match:
            xbmcgui.Dialog().ok(heading=addon.getLocalizedString(
                32000), message=addon.getLocalizedString(32078))
            return None
        recipients.append(recipient)

    recipients.extend(
        [addressbook[i] for i in selection if i < len(addressbook)])

    # update addressbook / change order so that most recent are on top
    new_addressbook = list(recipients)
    new_addressbook.extend(
        [address for address in addressbook if address not in recipients])
    addon.setSetting("output_emailaddress", "|".join(new_addressbook))

    return recipients


def send_email(folder: str, filename: str, recipients: 'list[str]') -> None:

    addon = xbmcaddon.Addon()
    for recipient in recipients:
        call = ["mail",
                "-A", os.path.join(folder, filename),
                "-s", f"{addon.getLocalizedString(32000)}: {filename}",
                recipient
                ]

        p = subprocess.Popen(call, stdout=subprocess.PIPE)
        p.wait()
        p.stdout.close()
