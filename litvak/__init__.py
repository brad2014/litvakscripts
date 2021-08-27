#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import sys
import re
import os

_session = None
_userId = None

BASE_URL = "https://donors.litvaksig.org/"


def _check_response(response, **kwargs):
    if response.status_code >= 400:
        raise ValueError(
            "HTTP returned bad status code {} for {}".format(
                response.status_code, response.url
            )
        )


def url(path="", baseUrl=BASE_URL):
    return baseUrl + path


def info(msg):
    print("INFO: " + msg, file=sys.stderr)


def fatal(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def login(username, password):
    global _session
    global _userId
    if _userId:
        return  # already logged in

    _session = requests.session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    }
    _session.headers.update(headers)
    _session.hooks["response"] = _check_response

    response = _session.post(
        url("process/_process_login.cfm"),
        data={
            "fl_usr": username,
            "fl_pss": password,
        },
        headers={"referer": BASE_URL},
    )
    if "msg=wrong" in response.url:
        fatal("Login failed. Invalid username and password")
    info("Login complete: {}".format(response.url))


def get(url, baseUrl=BASE_URL, **kwargs):
    global _session
    if not _session:
        login()
    return _session.get(baseUrl + url, **kwargs)


_xlsRe = re.compile(
    "/addons/photodownload[.]cfm[?]filename=([^&]+)&location=(\d+)&var=(\d+)"
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
