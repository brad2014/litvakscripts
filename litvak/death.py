#!/usr/bin/env python3

from .names import clean, extractSurname
from .person import buildFamily
from .normalize import (
    formatJulianAsGregorian,
    formatPlace,
    getParentsAge,
    getSpouseAge,
    calcBirthFromAge,
    commonFields,
    getWitnesses,
)
from .utils import warning


def processDeath(d):
    # A death record references the following people:
    #   principle (the deceased)
    #   Father
    #   paternal grandfather
    #   Mother
    #   maternal grandfather
    #   Spouse
    #   some witnesses
    #
    deceasedGiven = clean(d["given name"])
    deceasedSurname = d["surname"]
    spouseGiven = clean(d["spouse's given name"])
    spouseSurname = d["spouse's surname"]
    fatherGiven = d["father's given name"]

    # a few Death spreadsheets put a full name in the father gn field when
    # principle surname is a married name
    if spouseGiven and deceasedSurname:
        if not spouseSurname:
            spouseSurname = deceasedSurname
        if spouseSurname == deceasedSurname:
            # we don't know our (or dad's) surname if we are using our spouse's
            # this makes a ton of assumptions that death records list women
            # under their spouse's surname
            deceasedSurname = ""
    fatherGiven, deceasedSurname = extractSurname(fatherGiven, deceasedSurname)

    (
        deceased,
        father,
        fathersFather,
        mother,
        mothersFather,
        spouse,
        spouseFather,
    ) = buildFamily(
        deceasedGiven,
        deceasedSurname,
        fatherGiven,
        d.get("father's patronymic", ""),
        d["mother's given name"],
        d.get("mother's patronymic", ""),
        d["mother's maiden name"],
        spouseGiven,
        "",
        spouseSurname,
    )

    if deceased.gender and deceased.gender == spouse.gender:
        warning(
            "Deceased and spouse have same {} gender: {} and {}".format(
                deceased.gender, deceasedGiven, spouseGiven
            )
        )

    deceased.deathDate = formatJulianAsGregorian(d["y"], d["m"], d["d"])
    deceased.deathYear = d["y"]
    deceased.deathNote = ""
    deceased.deathPlace = formatPlace(d["town"], d["uyezd"], d["gubernia"])
    deceased.birthDate, deceased.birthYear, deceased.birthNote = calcBirthFromAge(
        deceased.deathYear, d["age"]
    )

    deceased.role = "Principle"

    fatherAge, motherAge = getParentsAge(d)
    witnesses = getWitnesses(d)

    father.birthDate, father.birthYear, father.birthNote = calcBirthFromAge(
        deceased.deathYear, fatherAge, genBirthYear=deceased.birthYear
    )
    father.role = "Father"

    mother.birthDate, mother.birthYear, mother.birthNote = calcBirthFromAge(
        deceased.deathYear, motherAge, genBirthYear=deceased.birthYear
    )
    mother.role = "Mother"

    (
        fathersFather.birthDate,
        fathersFather.birthYear,
        fathersFather.birthNote,
    ) = calcBirthFromAge(father.birthYear, None)
    fathersFather.role = "Father's Father"

    (
        mothersFather.birthDate,
        mothersFather.birthYear,
        mothersFather.birthNote,
    ) = calcBirthFromAge(mother.birthYear, None)
    mothersFather.role = "Mother's Father"

    spouseAge = getSpouseAge(d)
    # if age is not given, estimate spouse as roughly same generation
    spouse.birthDate, spouse.birthYear, spouse.birthNote = calcBirthFromAge(
        deceased.deathYear, spouseAge, genBirthYear=deceased.birthYear, generation=0
    )
    if "widow" in d["comments"].lower():
        spouse.deathDate = "before {}".format(d["y"])
        spouse.deathNote = "Spouse died a widow in {}.".format(d["y"])
    spouse.role = "Spouse"

    (
        spouseFather.birthDate,
        spouseFather.birthYear,
        spouseFather.birthNote,
    ) = calcBirthFromAge(spouse.birthYear, None)
    spouseFather.role = "Spouse's Father"

    rowCommon = commonFields(d, deceased.formatName(False))
    return [
        {**rowCommon, **p.normalizedFields()}
        for p in (
            deceased,
            father,
            fathersFather,
            mother,
            mothersFather,
            spouse,
            spouseFather,
            *witnesses,
        )
        if p
    ]
