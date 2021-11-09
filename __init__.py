"""ExpressVPN

Connect and Disconnect from ExpressVPN servers using the expresspn cli program"""


import subprocess
from collections import namedtuple
import albert

import os
import re

__title__ = "Express VPN"
__version__ = "0.4.0"
__triggers__ = "ev "
__authors__ = "@justanotherariel"
__exec_deps__ = ["expressvpn"]

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


VPNConnection = namedtuple(
    "VPNConnection", ["alias", "country", "location", "recommended"]
)
ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def getVPNConnections():
    consStr = subprocess.check_output(
        "expressvpn list all", shell=True, encoding="UTF-8"
    )
    conStrSplit = consStr.splitlines()
    print(conStrSplit)

    spacing_line_idx = None
    for line_idx, line in enumerate(conStrSplit):
        if line[0] == "-":
            spacing_line_idx = line_idx

    prev = None
    category_spacing = []
    for pos, char in enumerate(conStrSplit[spacing_line_idx]):
        print(char)
        if prev == " " and char == "-":
            category_spacing.append(pos)
        prev = char

    current_country = None
    for conStr in conStrSplit[spacing_line_idx:]:
        ## Alias
        alias = conStr[: category_spacing[0] - 1].strip()

        ## Country
        country = conStr[category_spacing[0] : category_spacing[1] - 1].strip()
        if country != "":
            current_country = country
        else:
            country = current_country

        ## Location
        location = conStr[category_spacing[1] : category_spacing[2] - 1].strip()

        ## Recommended
        recommended = conStr[category_spacing[2] :].strip()

        # albert.info([alias, country, location, recommended])
        yield VPNConnection(alias, country, location, recommended)


def buildItem(con):
    iconPath = os.path.join(__location__, "icons/earth.png")

    if con.alias == "smart":
        name = "smart"
    else:
        name = con.location

    text = f"Connect to {con.location}"
    commandline = ["expressvpn", "connect", con.alias]

    return albert.Item(
        id=f"expressvpn-{con.alias}",
        text=name,
        subtext=text,
        icon=iconPath,
        completion=name,
        actions=[albert.ProcAction(text=text, commandline=commandline)],
    )


def statusItem():
    statusStr = (
        subprocess.check_output("expressvpn status", shell=True, encoding="UTF-8")
        .splitlines()[0]
        .strip()
    )

    statusStr = ansi_escape.sub("", statusStr)

    albert.info(statusStr)

    item_text = ""
    item_subtext = ""
    commandline = ["expressvpn", "disconnect"]

    if "Connected to" in statusStr:
        item_text = "Disconnect"
        item_subtext = f"Connected to {statusStr[13:]}"
        iconPath = os.path.join(__location__, "icons/connected.png")
    elif "Reconnecting..." in statusStr:
        item_text = "Connection lost."
        item_subtext = "Reconnecting..."
        iconPath = os.path.join(__location__, "icons/reconnecting.png")
    elif "Unable to connect." in statusStr:
        item_text = "Unable to connect."
        item_subtext = "Check your internet connection."
        iconPath = os.path.join(__location__, "icons/disconnected.png")
    elif "Connecting..." in statusStr:
        item_text = "Connecting..."
        item_subtext = ""
        iconPath = os.path.join(__location__, "icons/disconnected.png")
    else:
        item_text = "Status"
        item_subtext = "Not connected"
        iconPath = os.path.join(__location__, "icons/disconnected.png")

    return albert.Item(
        id=f"vpn-disconnect",
        text=item_text,
        subtext=item_subtext,
        icon=iconPath,
        actions=[albert.ProcAction(text="disconnect", commandline=commandline)],
    )


def handleQuery(query):
    result = []

    if query.isValid and query.isTriggered:
        connections = getVPNConnections()

        if query.string == "":
            query.disableSort()

            result.append(statusItem())
            result.extend(
                [buildItem(con) for con in connections if con.recommended == "Y"]
            )

        else:
            result = [
                buildItem(con)
                for con in connections
                if (
                    query.string.lower() in con.country.lower()
                    or query.string.lower() in con.location.lower()
                )
            ]

        return result
    return []
