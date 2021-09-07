from enum import Enum

from .names import normalizeName, oppositeGender
from .utils import warning


class Gender(Enum):
    F = "F"
    M = "M"


class Person:
    def __init__(self, given, surname="", father=None, gender=None):
        self.sourceGiven = given
        self.sourceSurname = surname
        self.birthDate = self.birthPlace = self.birthNote = None
        self.deathDate = self.deathPlace = self.deathNote = None
        self.marriageDate = self.marriagePlace = self.marriageNote = None
        self.role = None

        if isinstance(father, Person):
            (
                self.normalizedGiven,
                self.normalizedPatronym,
                self.normalizedSurname,
                self.gender,
            ) = normalizeName(
                self.sourceGiven,
                father.sourceGiven,
                father.sourceSurname,
                gender,
            )
        else:
            (
                self.normalizedGiven,
                self.normalizedPatronym,
                self.normalizedSurname,
                self.gender,
            ) = normalizeName(
                self.sourceGiven,
                "",
                self.sourceSurname,
                gender,
            )
        if not isinstance(father, Person):
            return
        if self.normalizedPatronym:
            if (father.normalizedGiven and father.normalizedGiven.lower() !=
                    self.normalizedPatronym.lower()):
                warning("{} has patronym {} != father's given name {}.".format(
                    self.formatName(False),
                    self.normalizedPatronym,
                    father.normalizedGiven,
                ))
            elif not father.normalizedGiven:
                father.normalizedGiven = self.normalizedPatronym
                father.normalizedPatronym = ""
        if self.normalizedSurname:
            if (father.normalizedSurname and father.normalizedSurname.lower()
                    != self.normalizedSurname.lower()):
                warning("{} has surname {} != father's surname {}.".format(
                    self.formatName(False),
                    self.normalizedSurname,
                    father.normalizedSurname,
                ))
            else:
                father.normalizedSurname = self.normalizedSurname

    def __bool__(self):
        return True if self.normalizedGiven else False

    def formatName(self, normalize=False):
        if not self:
            return ""
        if normalize:
            if self.normalizedPatronym:
                prefix = "bat" if self.gender == "F" else "ben"
                p = " {} {}".format(prefix, self.normalizedPatronym)
            else:
                p = ""
            return "{}{} /{}/".format(self.normalizedGiven, p,
                                      self.normalizedSurname).strip()
        return "{} {}".format(self.sourceGiven, self.sourceSurname).strip()

    def normalizedFields(self):
        return {
            "Source Given Name": self.sourceGiven,
            "Source Surname": self.sourceSurname,
            "Name": self.formatName(True),
            "Gender": self.gender,
            "Birth Date": self.birthDate,
            "Birth Note": self.birthNote,
            "Birth Place": self.birthPlace,
            "Death Date": self.deathDate,
            "Death Note": self.deathNote,
            "Death Place": self.deathPlace,
            "Marriage Date": self.marriageDate,
            "Marriage Place": self.marriagePlace,
            "Role": self.role,
        }

    #
    # for debugging
    #
    def dump(self):
        from inspect import getmembers
        from pprint import pprint

        pprint(getmembers(self))


# build the names of a common family group: child, two parents, with patronyms.
def buildFamily(
    givenName,
    surname,
    fatherGiven,
    paternalPatronymic,
    motherGiven,
    maternalPatronymic,
    motherMaidenName,
    spouseGiven="",
    spousePatronymic="",
    spouseSurname="",
    gender=None,
):
    # Normalize them from oldest generation to youngest
    mothersFather = Person(maternalPatronymic, motherMaidenName, None, "M")
    fathersFather = Person(paternalPatronymic, surname, None, "M")
    spousesFather = Person(spousePatronymic, spouseSurname, None, "M")
    mother = Person(motherGiven, motherMaidenName, mothersFather, "F")
    father = Person(fatherGiven, surname, fathersFather, "M")
    principal = Person(givenName, surname, father, gender)
    spouse = Person(spouseGiven,
                    spouseSurname,
                    spousesFather,
                    gender=oppositeGender(gender))

    return (
        principal,
        father,
        fathersFather,
        mother,
        mothersFather,
        spouse,
        spousesFather,
    )
