#!/usr/bin/env python3

import os
import re
from bs4 import BeautifulSoup
from .utils import get, info

_xlsRe = re.compile(
    r"/addons/photodownload[.]cfm[?]filename=([^&]+)&location=(\d+)&var=(\d+)"
)


def getFileList(group):
    info("Scanning for site files: {}".format(group))
    fileList = {}
    response = get("site/" + group)
    soup = BeautifulSoup(response.content, "html.parser")
    for link in soup.find_all("a", {"class": "excel"}):
        match = _xlsRe.search(link["onclick"])
        if not match:
            continue
        basename, location, var = match.groups()
        fileList[basename] = {"filename": basename, "location": location, "var": var}
    info("Found {} files".format(len(fileList)))
    return fileList


def downloadXlsFile(outdir, group, params, overwrite, dryrun):
    fileName = os.path.join(outdir, params["filename"])
    os.makedirs(outdir, exist_ok=True)
    if os.path.exists(fileName) and not overwrite:
        info("File exists - skipping: {}".format(fileName))
        return
    if dryrun:
        info("Dry run - would download: {}".format(fileName))
        return
    info("Saving {}...".format(fileName))
    stream = get("addons/photodownload.cfm", stream=True, params=params)
    with open(fileName, "wb") as f:
        for chunk in stream.iter_content(1024):
            f.write(chunk)
