import os
from .utils import info, warning, setWarningContext
from xlrd import open_workbook

# from pprint import pprint

#
# This is very hacky, and based on an analysis of all the spreadsheets produced
# by litvaksig. It basically attempts to normalize them into a single template.
#

# different ways column names appear in the spreadsheets, and a normalized version
_keyMap = {
    "w1": "witness 1",
    "w2": "witness 2",
    "w3": "witness 3",
    "3.0": "witness 3",
    "4.0": "witness 4",
    "age / yr. born": "age",
    "age*": "wife's age",
    "age/ yr. born": "age",
    "age /year born": "age",
    "day": "d",
    "district": "uyezd",
    "father's father": "father's patronymic",
    "father's given name*": "wife's father's given name",
    "father's patronymic*": "wife's father's patronymic",
    "father": "father's given name",
    "gf": "father's patronymic",
    "ff": "father's patronymic",
    "mf": "mother's patronymic",
    "given name*": "wife's given name",
    "guberniya": "gubernia",
    "husband's given name": "given name",
    "husband's surname": "surname",
    "husband's father's given name": "father's given name",
    "husband's mother's given name": "mother's given name",
    "husband's maternal grandfather": "mother's patronymic",
    "husband's paternal grandfather": "father's patronymic",
    "husband's mother's maiden name": "mother's maiden name",
    "husband's place": "place",
    "town, uyezd": "place",
    "husband's age": "age",
    "maternal grandfather": "mother's patronymic",
    "maternal grandfather*": "wife's mother's patronymic",
    "month": "m",
    "mother's father": "mother's patronymic",
    "mother's given name*": "wife's mother's given name",
    "mother's given name|father's patronymic": "mother's patronymic",
    "mother's given name|pat": "mother's patronymic",
    "mother's maiden name*": "wife's mother's maiden name",
    "mother's maiden surname": "mother's maiden name",
    "mother's patronymic*": "wife's mother's patronymic",
    "mother": "mother's given name",
    "paternal grandfather": "father's patronymic",
    "paternal grandfather*": "wife's father's patronymic",
    "spouse surname": "spouse's surname",
    "spouse": "spouse's given name",
    "surname*": "wife's surname",
    "wife's mother's given name|": "wife's mother's patronymic",
    "wife's maternal grandfather": "wife's mother's patronymic",
    "wife's paternal grandfather": "wife's father's patronymic",
    "witness": "witness 1",
    "witness1": "witness 1",
    "witness2": "witness 2",
    "witness3": "witness 3",
    "witness4": "witness 4",
    "witness 1": "witness 1",
    "witness 2": "witness 2",
    "witness 3": "witness 3",
    "witness 4": "witness 4",
    "w1": "witness 1",
    "w2": "witness 2",
    "w3": "witness 3",
    "w4": "witness 4",
    "comments (witness ii, age)": "witness 2",
    "other surnames (wittness i, age)": "witness 1",
    "descendants": "comments",
    "year": "y",
    "comments|": "source: archive / fond / list / item",
    "source: archive/fond/list/item": "source: archive / fond / list / item",
    "wife's father's given name|": "wife's father's patronymic",
    "wife's mother's given name|patronymic": "wife's mother's patronymic",
    # "other towns|": "comments",
}


fileTypeMap = {
    "child's surname": "Birth",
    "marriage or divorce": "Marriage",
    "cause of death": "Death",
}


def getRowHeader(xlsFileName, row):
    header = []
    info("File columns for: {}".format(xlsFileName))
    last = ""
    for i, k in enumerate(row):
        # hack bad column names
        k = " ".join(str(k).split()).lower()
        k = _keyMap.get(k, k)

        # hack column names that depend on preceding column
        k = _keyMap.get(last + "|" + k, k)

        while k in header:
            k += "*"
            k = _keyMap.get(k, k)
        header.append(k)
        last = k
        info(" {:2d}. {}".format(i, k))
    return header


def xlsRows(xlsFileName):
    wb = open_workbook(xlsFileName)
    header = None
    fileType = None
    baseName = os.path.basename(xlsFileName)
    # Sometimes the first sheet is a cover sheet, sometimes it is data
    if "Chronological" in wb.sheet_names():
        sh = wb.sheet_by_name("Chronological")
    else:
        sh = wb.sheet_by_index(0)

    # Iterate over all the rows, looking for a good header row
    # (it is usually in row 1,2 or 3)
    for rowNum in range(sh.nrows):
        setWarningContext(xlsFileName, rowNum + 1)
        row = sh.row_values(rowNum)
        if "Record #" in row:
            header = getRowHeader(baseName, row)
            # Determine what kind of records this file contains,
            # based on an indicative column.
            for type, value in fileTypeMap.items():
                if type in header:
                    fileType = value
                    break
            if not fileType:
                warning("Unknown file type. {}".format(xlsFileName))
                return
            continue
        if not fileType:
            continue
        d = {
            k: row[i].strip() if isinstance(row[i], str) else int(row[i])
            for i, k in enumerate(header)
        }
        d["rowNum"] = rowNum + 1
        d["fileName"] = baseName
        d["fileType"] = fileType
        if "year recorded" not in d:
            d["year recorded"] = d["y"]
        if not d["y"]:
            d["y"] = d["year recorded"]
        yield d
    setWarningContext("", "")
