import requests
import sys

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


_curFileName = ""
_curRow = ""


def setWarningContext(fileName, row):
    global _curFileName, _curRow
    _curFileName = fileName
    _curRow = row


def info(msg):
    print("{}:{} INFO: {}".format(_curFileName, _curRow, msg), file=sys.stderr)


def warning(msg):
    global _curFileName, _curRow
    print("{}:{} WARNING: {}".format(_curFileName, _curRow, msg), file=sys.stderr)


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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)"
        " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
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
