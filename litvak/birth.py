#
from .person import buildFamily
from .normalize import (
    formatPlace,
    formatJulianAsGregorian,
    getParentsAge,
    calcBirthFromAge,
    getWitnesses,
    commonFields,
)
import re

_twinsRe = re.compile(
    r"""
        ^\s*
        twins:\s*
        ([\w\s]+)\s*
        (?:&|and)\s*
        ([\w\s]+)
    """,
    flags=re.I + re.X,
)


def processBirth(d):
    # A birth record references the following people:
    #   principle (the child)
    #   Father
    #   paternal grandfather
    #   Mother
    #   maternal grandfather
    #   some witnesses
    #
    if "twin name" not in d:
        match = _twinsRe.search(d["child's given name"])
        if match:
            return [
                processBirth({**d, "twin name": match.group(1)})[0],
                *processBirth({**d, "twin name": match.group(2)}),
            ]

    (child, father, fathersFather, mother, mothersFather, skip, skip) = buildFamily(
        d.get("twin name", d["child's given name"]),
        d["child's surname"],
        d["father's given name"],
        d["father's patronymic"],
        d["mother's given name"],
        d["mother's patronymic"],
        d["mother's maiden name"],
    )

    # Set roles
    child.birthDate = formatJulianAsGregorian(d["y"], d["m"], d["y"])
    child.birthNote = ""
    child.birthPlace = formatPlace(d["town"], d["uyezd"], d["gubernia"])
    child.role = "Principle"

    fatherAge, motherAge = getParentsAge(d)
    father.birthDate, father.birthYear, father.birthNote = calcBirthFromAge(
        d["y"], fatherAge
    )
    father.role = "Father"

    mother.birthDate, mother.birthYear, mother.birthNote = calcBirthFromAge(
        d["y"], motherAge
    )
    mother.role = "Mother"

    (
        fathersFather.birthDate,
        fathersFather.birthYear,
        fathersFather.birthNote,
    ) = calcBirthFromAge(father.birthYear, None, genBirthYear=father.birthYear)
    fathersFather.role = "Father's Father"

    (
        mothersFather.birthDate,
        mothersFather.birthYear,
        mothersFather.birthNote,
    ) = calcBirthFromAge(mother.birthYear, None)
    mothersFather.role = "Mother's Father"

    witnesses = getWitnesses(d)
    rowCommon = commonFields(d, d["child's given name"] + " " + d["child's surname"])
    return [
        {**rowCommon, **p.normalizedFields()}
        for p in (
            child,
            father,
            fathersFather,
            mother,
            mothersFather,
            *witnesses,
        )
        if p
    ]
