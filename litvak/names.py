#!/usr/bin/env python3

#
#  Normalize Hebrew/Litvak Names - Extracted from LitvakSig.org spreadsheets
#
# normalize names: gender, and alternative spellings
# Refs:
# https://bloodandfrogs.com/2011/06/variations-in-jewish-given-names.html
# https://www.jewishgen.org/databases/GivenNames/search.htm
#
import re
from .namelist import nameList
from .utils import warning, info, fatal


# map raw name (titlecase) to normalized name (uppercase):
nameMap = {"M": {}, "F": {}, "S": {}, "P": {}}
genderSet = {"M": set(), "F": set()}


def initNameMaps():
    for (cooked, gender, rawList) in nameList:
        cooked = cooked.upper()
        gender = gender.upper()
        if gender in genderSet:
            genderSet[gender].add(cooked)
        nameMap[gender][cooked.title()] = cooked
        if not isinstance(rawList, tuple):
            fatal("Malformed namelist: {}".format(cooked))
        for raw in rawList:
            nameMap[gender][raw.title()] = cooked


initNameMaps()
# extract patronyms ('x son of y', 'x yowicz') from a raw name

# The raw given name might contain a patronym, which we separate out.
# Chaia Leah Abramowicz
# Aizik, son of Chaim
# Chaia of Yudel
#
_patronymRe = re.compile(
    r"""
        ^\s*
        ([\w\s]+?\w) # gn
        (?:[,\s](?:a\s)?)?\s* # optional "," or ", a "
        (?:
            (son|dau\w*|bar|ben|bat)\s+ # gender mark: son/daughter
            (?:of\s+)?  # optional of
            ([\w\s]+\w) # pn1
            |
            (\w+) # pn2
            (?:owicz|ovitz|ovich)
            |
            (?:of\s+) # required of ()
            ([\w\s]+\w) # pn3 unmarked patronym
        )
        (?:[.,;?].*)?
        \s*$
    """,
    flags=re.I + re.X,
)

# match Irsas Leibas ZUPOVICIUS / [ZUPOVICH] => Irsas Leibas, ZUPOVICH
_surnameRe = re.compile(
    r"""
        ^\s*
        (?:)
        ([\w\s]+?\w)\s+ # gn
        (?:[A-Z]+\s*/\s*)? # optional lithunaian version
       \[?               # optional brackets
       ([A-Z]+)         # sn in uppercase
       \]?
       \s*$
    """,
    flags=re.X,
)


def clean(nameRaw):
    if not nameRaw:
        return ""
    # Some cleanup:
    # change Irsas JANKAVICIUS / [IANKOVICH] to   Irsas IANKOVICH
    nameRaw = re.sub(r"(\w+)\s+\w+\s*/\s*\[(\w+)\]", r"\1 \2", nameRaw)
    # a name in brackets is always preferred
    nameRaw = re.sub(r".*\[(\w )+\].*", r" \1 ", nameRaw)
    # If a/b, use b (lithuanian, alternates)
    nameRaw = re.sub(r".*/", "", nameRaw)
    # Remove bad characters
    nameRaw = re.sub(r"\W+", " ", nameRaw)
    return nameRaw.strip()


def normalizeName(gn, pn="", sn="", gender=None, dump=False):
    def mapRawName(nameRaw, gender=None):
        global nameMap
        # assume patronymics have been removed, and we're left with a string of
        # names "Chaia Leah". You can tell a name is mapped if it is in
        # UPPERCASE.  Unmappable names are in Title Case.
        subNames = clean(nameRaw).title().split()
        if gender:
            return (
                " ".join([nameMap[gender].get(name, name) for name in subNames]),
                gender,
            )

        # maybe one of the subnames tells us the gender of the whole name
        genSet = set()
        for name in subNames:
            isM = name in nameMap["M"]
            isF = name in nameMap["F"]
            if isM and not isF:
                genSet.add("M")
            elif isF and not isM:
                genSet.add("F")
        if genSet == {"M"}:
            gender = "M"
        elif genSet == {"F"}:
            gender = "F"
        elif genSet == {"M", "F"}:
            warning(
                "name '{}' has a mix of male-only and female-only names".format(nameRaw)
            )
            gender = "M"  # later, fix the name list
        else:
            return nameRaw, None  # nameList has nothing, or gender is ambiguous

        return (
            " ".join([nameMap[gender].get(name, name) for name in subNames]),
            gender,
        )

    #
    # The gn and pn may be returned unchanged, or, if the raw string contains a
    # embedded patronym, the patronym will be moved to pn (overwriting what was there).
    #
    def extractPatronym(gnRaw, pnRaw, gender):
        gn, pn = str(gnRaw), str(pnRaw)
        match = _patronymRe.search(gn)
        gmark = None
        if match:
            gn, gmark, pn1, pn2, pn3 = match.groups()
            pn = pn1 or pn2 or pn3
        if pnRaw and pn.upper() != str(pnRaw).upper():
            warning(
                "Name {} has two patronyms: {} overwrites {}".format(gnRaw, pn, pnRaw)
            )
        if gmark:
            # update gender based on patronym gender mark: son of, dau of
            gmarkNormalized = gmark[0:3].lower()
            if gmarkNormalized in ("son", "bar", "ben"):
                if not gender or gender == "M":
                    gender = "M"
                elif gender:
                    warning(
                        "Name {} has patronym gender: {}, expected {}".format(
                            gnRaw, gmark, gender
                        )
                    )
            elif gmarkNormalized in ("dau", "bat"):
                if not gender or gender == "F":
                    gender = "F"
                elif gender:
                    warning(
                        "Name {} has patronym gender: {}, expected {}".format(
                            gnRaw, gmark, gender
                        )
                    )

        return gn, pn, gender

    gn, sn = extractSurname(gn, sn)
    # gender is explicit in given name via embedded patronym:  e.g. Hanna, dau. of Aisik
    gn, pn, gender = extractPatronym(gn, pn, gender)
    gn, gender = mapRawName(gn, gender)

    # Sometimes a father name ends up in the surname field.
    # Of course, a surname could be the same as a male name, but, oh well.
    if not pn and sn in nameMap["M"]:
        pn = sn
        sn = ""

    # Sometimes a name with patronym ends up in the father's given name field.
    # We can discard it, since buildFamily will find a home for it.
    # extractPatronym(gn, pn, gender)
    pn, skip, skip = extractPatronym(pn, "", "M")  # not used: ppn

    pn, skip = mapRawName(pn, "M")
    sn, skip = mapRawName(sn, "S")

    if dump:  # for debugging
        for n in gn.split():
            info("NAME:{}:{}".format(gender, n))
        for n in pn.split():
            info("NAME:{}:{}".format("M", n))
        for n in sn.split():
            info("NAME:{}:{}".format("S", n))

    return (gn, pn, sn, gender)


def extractSurname(gnRaw, snRaw):
    gn, sn = str(gnRaw), str(snRaw)
    match = _surnameRe.search(gn)
    if match:
        gn, sn = match.groups()
    if snRaw and sn != snRaw:
        "NOTE: {} {} surname changed to {} {}".format(gnRaw, snRaw, gn, sn)
    return gn, sn


def oppositeGender(gender):
    if gender == "M":
        return "F"
    elif gender == "F":
        return "M"
    return None


# guess the gender of a raw name
def guessGender(gn, spouse=None):
    gn, pn, sn, gender = normalizeName(gn, "", "")
    if spouse and not gender:
        # if name doesn't indicate gender, try for opposite of spouse gender
        gn, pn, sn, spouseGender = normalizeName(spouse, "", "")
        gender = oppositeGender(spouseGender)
    return gender


def parseName(name):
    parseNameRe = re.compile(
        r"""
        ^\s*
        ([\w ]+?\w)\s*
        (?:
            (?:ben|bat)\s+
            ([\w ]+\w)\s+
        )?
        /([^/]*)/
        \s*$
        """,
        re.I + re.X,
    )
    match = parseNameRe.search(name)
    if not match:
        raise ValueError("parseName: invalid name: {}".format(name))
    return match.groups()


# return score in [0:1] for "confidence" that two names are the same individual
def nameScore(n1, n2):
    if not n1 or not n2:
        return 0

    # score a single name part
    def multiNameScore(n1, n2):
        if not n1 or not n2:
            return 0.5
        n1set = set(n1.split())  # set: ignores spaces and order
        n2set = set(n2.split())
        if n1set == n2set:
            return 1  # exact match
        if n1set < n2set or n2set > n1set:
            return 0.75  # one name is subset of the other ('chasha' ⊂ "chasha leah")
        return 0  # ('chasha leah' ≠ 'chasha rebecca')

    # Quick Check: names match exactly?
    if n1 == n2:
        score = 1
    else:
        gn1, pn1, sn1 = parseName(n1)
        # print("Name1: {} ~ {} ~ {}".format(gn1, pn1, sn1))
        gn2, pn2, sn2 = parseName(n2)
        score = (
            multiNameScore(sn1, sn2)
            * multiNameScore(pn1, pn2)
            * multiNameScore(gn1, gn2)
        )
    # if score > 0:
    #     print("SCORE: '{}' ? '{}' = {:.2f}".format(n1, n2, score))
    return score
