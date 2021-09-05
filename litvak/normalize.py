import re
from .person import Person
from .utils import warning, info

# output field, and description
fieldInfo = (
    ("File", "The name of the source spreadsheet for this record"),
    ("Row", "The spreadsheet row number on which this record appears."),
    ("Source Description", "A brief description that identifies the record."),
    ("Name", "The normalized name of an individual mentioned in a record."),
    ("Gender", "Male, Female, or Unknown. An educated guess based on role and name."),
    ("Role", "The role of the individual with respect to this record."),
    ("Birth Date", "The date of birth. Gregorian calendar. May be approximate."),
    (
        "Birth Note",
        "If approximate, how it was derived (e.g. from age, "
        "or relation to child or spouse)",
    ),
    ("Birth Place", "The town, district, province of the birth."),
    ("Death Date", "The date of death. Gregorian calendar."),
    (
        "Death Note",
        "If approximate, how it was derived (e.g. from age, or relation to spouse)",
    ),
    ("Death Place", "The town, district, province of the death."),
    ("Marriage Date", "The date of marriage. Gregorian calendar."),
    ("Marriage Place", "The town, district, province of the marriage."),
    ("Source", "As indicated on the spreadsheet, typically archive/fond/list/item"),
    ("Microfilm", "As indicated on the spreadsheet"),
    ("Recorded On", "Year recorded, in source spreadsheet."),
    ("Recorded At", "Place recorded, in source spreadsheet."),
    ("Record Number", "Record number in source spreadsheet."),
    ("Source Given Name", "The raw given name from the source record."),
    ("Source Surname", "The raw surname from the source record."),
    (
        "Source Date",
        "The event date as it is in the source record, Julian Day/Month/Year.",
    ),
    (
        "Source Place",
        "The event place as it is in the source record, Town, Uyezd, Gubernia",
    ),
    ("Errors", "Description"),
)

fieldNames = (x[0] for x in fieldInfo)

monthNames = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

_parentAgeInCommentsRe = re.compile(
    r"""
        father.*\s(\d+)[,.].*mother\s*(\d+)
    """,
    flags=re.I + re.X,
)
_spouseAgeInCommentsRe = re.compile(
    r"""
        (?:husb\w+|wife)[,\s]\s*(\d+)
    """,
    flags=re.I + re.X,
)

_witnessRe = re.compile(
    r"""
        ^\s*
        ((?:\w+\s+)*\w+),\s*  # full name (followed by comma)
        (?:\w+\s*,\s*)?       # optional occupation, ignored
        (\d+)                 # age
    """,
    flags=re.I + re.X,
)


def formatJulianAsGregorian(Y, M, D):
    def cleanNum(v):
        if v is None:
            return 0
        if isinstance(v, str):
            # some spreadsheets put gregorian values in parens - remove them
            v = re.sub(r"\(.*\)", "", v)
            v = re.sub(r"[^\d]", "", v)  # remove non-numerics like '?'
            v = v or 0  # missing is represented by zero
        return int(v)

    # convert raw month field text to month number 1-12
    def cleanMonth(v):
        if isinstance(v, str):
            monName = v[0:3].title()
            if monName in monthNames:
                return monthNames.index(monName) + 1
        return cleanNum(v)

    Y = cleanNum(Y)
    M = cleanMonth(M)
    D = cleanNum(D)
    if not D and not M:
        return str(Y)
    if not M:
        return "{}-{}".format(M, Y)

    # Convert to Julian Day, then convert that to Gregorian Y-M-D
    # Utterly inscrutable code from the wikipedia page.  Seems legit.
    # Ref: https://en.wikipedia.org/wiki/Julian_day#Julian_day_number_calculation
    J = 367 * Y - (7 * (Y + 5001 + (M - 9) // 7)) // 4 + (275 * M) // 9 + D + 1729777
    y = 4716
    j = 1401
    m = 2
    n = 12
    r = 4
    p = 1461
    v = 3
    u = 5
    s = 153
    w = 2
    B = 274277
    C = -38
    f = J + j + (((4 * J + B) // 146097) * 3) // 4 + C
    e = r * f + v
    g = (e % p) // r
    h = u * g + w
    D = ((h % s)) // u + 1
    M = ((h // s + m) % n) + 1
    Y = (e // p) - y + (n + m - M) // n
    return "{:04d}-{:02d}-{:02d}".format(Y, M, D)


def formatPlace(town, district, province):
    return ",".join([town, district, province])


_ageRe = re.compile(
    r"""
        ^\s*
        (?:
            (\d+)\s*
            (?:
                (da|we|mo|ye)\w*
            )?
            |newborn
            |stillborn
            |\d\s\d(?:\sye\w*)?    # a cleaned fraction or decimal 1/2 or 1,5
        )
        \s*$
    """,
    flags=re.I + re.X,
)

_ageAsDateRe = re.compile(
    r"""
        (?: (\d{1,2})\s+)?
        (?: (\w{3})\w*\s+)?
        (?: (\d{1,2})\s+)?
        (\d{4})
        \s*$
    """,
    flags=re.I + re.X,
)

MINYEAR = 1000

#
# Lots of possiblities:
# raage is either an exact year, or an age with respect to the given year
# If there is no age, we calculate the birth as some generational distance
# prior to the genBirthYear
# For example, the father of the bride might be age 50:
# birth is 50 before marriage date.
# Or his age might not be given:
# in which case he is one generation (say 25 years) before the bride's birth year.


def calcBirthFromAge(
    yearRaw, ageRaw=None, generation=1, genBirthYear=None, genYears=25
):
    def clean(v):
        v = str(v)
        # remove parenthesized values
        v = re.sub(r"\(.*\)", "", str(v))
        # remove non-word characters and multiple spaces
        return re.sub(r"[^\w\s]+", " ", v)

    def extractNum(v):
        if isinstance(v, int):
            return v
        v = clean(v)
        v = re.sub(r"[^\d].*", "", v)  # pick out first number
        if v == "":
            return -1  # marker: no value
        return int(v)

    def dateInAgeField(ageRaw):
        match = _ageAsDateRe.search(clean(ageRaw))
        if not match:
            return None
        return (
            formatJulianAsGregorian(
                match.group(4), match.group(2), match.group(3) or match.group(1)
            ),
            int(match.group(4)),
            "Given: {} (Julian)".format(ageRaw),
        )

    def dateBasedOnAgeAndYear(ageRaw, yearRaw):
        # try to interpret the age field as a number with optional units (3 months)
        age = clean(ageRaw)
        match = _ageRe.match(age)
        if not match:
            return None
        num, unit = match.groups()
        if unit and unit != "ye" or not num:
            # All sub-years round to zero.
            # Calculated birthdates should be read as +/- 1 year.
            num = 0
        num = int(num)
        if not 0 <= num < 120:  # ignore crazy ages
            warning("Impossible age: {}".format(ageRaw))
        if not yearRaw:
            info("Age but no base year: {}, {}".format(ageRaw, yearRaw))
        year = extractNum(yearRaw)
        if year == -1:
            info("Age but no base year: {}, {}".format(ageRaw, yearRaw))
        elif year < MINYEAR:
            warning("Impossible year: {} ({})".format(yearRaw, year))
        return (
            "{}".format(year - num),
            year - num,
            "Calculated: age {} in {}".format(ageRaw, yearRaw),
        )

    def estimateBirthFromGeneration(genBirthYear, generation, genYears):
        year = extractNum(genBirthYear)
        if year < MINYEAR:
            return None
        return (
            "{}".format(year - generation * genYears),
            year - generation * genYears,
            "Estimated: {} gen before {}".format(generation, genBirthYear),
        )

    if ageRaw:
        # try to interpret the age field as an actual date
        result = dateInAgeField(ageRaw)
        if result:
            return result
        result = dateBasedOnAgeAndYear(ageRaw, yearRaw)
        if result:
            return result
    genBirthYear = genBirthYear or yearRaw
    if genBirthYear:
        yearRaw
        result = estimateBirthFromGeneration(genBirthYear, generation, genYears)
        if result:
            return result
        warning("Unable to process birth year for estimate: {}".format(genBirthYear))
    return None, None, None


def commonFields(d, principalName):
    return {
        "File": d["fileName"],
        "Row": d["rowNum"],
        "Source": d["source: archive / fond / list / item"],
        "Microfilm": d["microfilm #"],
        "Recorded On": d["year recorded"],
        "Recorded At": d["place recorded"],
        "Record Number": d["record #"],
        "Source Date": "/".join([str(d["d"]), str(d["m"]), str(d["y"])]),
        "Source Place": ",".join([d["town"], d["uyezd"], d["gubernia"]]),
        "Source Description": "{} of {} in {} {}".format(
            d["fileType"], principalName, d["y"], d["town"]
        ).strip(),
    }


def getParentsAge(d):
    #
    fatherAge = d.get("father's age", None)
    motherAge = d.get("mother's age", None)
    match = _parentAgeInCommentsRe.search(str(d["comments"]))
    if match:
        fatherAge = match.group(1)
        motherAge = match.group(2)
    return fatherAge, motherAge


def getSpouseAge(d):
    spouseAge = d.get("spouse's age", None)
    match = _spouseAgeInCommentsRe.search(str(d["comments"]))
    if match:
        spouseAge = match.group(1)
    return spouseAge


def getWitnesses(d):
    witnesses = []
    for w in [s for s in d.keys() if s.startswith("witness")]:
        match = w in d and _witnessRe.search(d[w])
        if match:
            gn, age = match.groups()
            p = Person(gn)
            p.role = "Witness"
            p.birthDate, skip, p.birthNote = calcBirthFromAge(d["y"], age)
            witnesses.append(p)
    return witnesses
