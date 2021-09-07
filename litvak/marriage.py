#!/usr/bin/env python3

# Return all the individuals for a Marriage record
from .normalize import (calcBirthFromAge, commonFields,
                        formatJulianAsGregorian, formatPlace, getParentsAge,
                        getWitnesses)
from .person import buildFamily


def processSpouseFam(d, side="Husband", dprefix=""):

    (spouse, father, fathersFather, mother, mothersFather, skip,
     skip) = buildFamily(
         d[dprefix + "given name"],
         d[dprefix + "surname"],
         d[dprefix + "father's given name"],
         d.get(dprefix + "father's patronymic", ""),
         d[dprefix + "mother's given name"],
         d.get(dprefix + "mother's patronymic", ""),
         d[dprefix + "mother's maiden name"],
     )

    age = d[dprefix + "age"]
    spouse.birthDate, spouse.birthYear, spouse.birthNote = calcBirthFromAge(
        d["y"], age)
    spouse.role = side
    spouse.birthPlace = d[dprefix + "place"]

    spouse.marriageDate = formatJulianAsGregorian(d["y"], d["m"], d["d"])
    spouse.marriageYear = d["y"]
    spouse.marriagePlace = formatPlace(d["town"], d["uyezd"], d["gubernia"])

    fatherAge, motherAge = getParentsAge(d)
    father.birthDate, father.birthYear, father.birthNote = calcBirthFromAge(
        d["y"], fatherAge, genBirthYear=spouse.birthYear)
    father.role = side + "'s Father"

    mother.birthDate, mother.birthYear, mother.birthNote = calcBirthFromAge(
        d["y"], motherAge, genBirthYear=spouse.birthYear)
    mother.role = side + "'s Mother"

    (
        fathersFather.birthDate,
        fathersFather.birthYear,
        fathersFather.birthNote,
    ) = calcBirthFromAge(father.birthYear, None)
    fathersFather.role = side + "'s Father's Father"
    (
        mothersFather.birthDate,
        mothersFather.birthYear,
        mothersFather.birthNote,
    ) = calcBirthFromAge(mother.birthYear, None)
    mothersFather.role = side + "'s Mother's Father"
    return (spouse, father, fathersFather, mother, mothersFather)


def processMarriage(d):

    # HUSBAND FAMILY

    husbFam = processSpouseFam(d, "Husband", "")
    wifeFam = processSpouseFam(d, "Wife", "wife's ")
    witnesses = getWitnesses(d)
    rowCommon = commonFields(
        d,
        "{} {} & {} {}".format(d["given name"], d["surname"],
                               d["wife's given name"], d["wife's surname"]),
    )

    return [{
        **rowCommon,
        **p.normalizedFields()
    } for p in (
        *husbFam,
        *wifeFam,
        *witnesses,
    ) if p]
