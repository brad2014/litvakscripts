# LitvakScripts

Python scripts I use for manipulating and analyzing data collected by the LitvakSIG team.

They currently focus on aggregating and normalizing that data, to make it easier to search and compare.

They incorporate a lot of collected insights about things like how yiddish names work, and how dates are recorded, and how these particular records were transcribed and turned into spreadsheets. I'm open to suggestions on what would make them more useful to genealogists with technical chops who are interested in this data.

Note: My scripts read data (i.e. spreadsheets) that are developed, copyrighted and published by [LitvakSIG, Inc.](https://www.litvaksig.org) Accessing their data requires an account on their web site, and use of their data is subject to their terms of use.  To get access, [join LitvakSig!](https://www.litvaksig.org/membership-and-contributions/join-and-contribute/)

## Installation / Setup


The scripts run with python3 and virtualenv.  For information on how to install those, see python.org.

```sh
% virtualenv -p python3 .virtualenv
% source .virtualenv/bin/activate
% pip install -r requirements.py
```

## Downloading Spreadsheets

Download some or all of the spreadsheets from a LitvakSIG group, to which your account has access.  Use the -h flag for help.  To see what files are available, without downloading them, use the --dry-run flag.

You can set the LITVAK_USERNAME and LITVAK_PASSWORD environment variables to your account login credentials, in lieu of repeatedly specifying them on the command line.

For detailed usage information, invoke with the help flag.

```sh
% ./DownloadSpreadsheets -h
```


## Normalizing spreadsheets

Read any number of birth/death/marriage spreadsheets (other spreadsheets can be in the list, they will currently be ignored - maybe later we'll extract age/residence info). Output a consolidated CSV file.  

### Description

The spreadsheet files are opaque to automated processing, and there is substantial variation in the table formats (what information is provided for each record), column headers are labeled differently, key elements are buried in text comments, and names are spelled in many different ways (the original records vary, the transliterations vary, changes were introduced at every step).  

This program attempts to make the large number of educated guesses to consolidate and normalize all that material.

Note: The normalization process is not intended to replace access to the sources, it is specifically designed ease search and comparison.

### Output

The resulting CSV file includes one line for each individual matched by each input record.  For example, a birth record may generate output rows for the child, the mother and father, the grandfathers (if patronymics are given).  

The output columns are divided into groups:

1. The source record - Spreadsheet name and row.
2. Name, Gender, Role - the individual referenced in the source record.  The names are mapped to a common normal form, using educated guesses to align all the variant spellings and typos found in the source material (often by mapping a variety of Yiddish nicknames to their Hebrew origin).  Roles are things like "father", "wife", "witness".  Gender is either inferred from role, or is an educated guess based on a (gendered) name - it is not explicitly marked in the source records.
3. Dates and places - Birth, Death, Marriage, whichever are given or estimatable from the source record. We can almost always estimate a birth date: either it is given in the record, or an age is given (perhaps buried in the comments!) from which we can calculate an estimate, or failing that, we can pick a year based on the individual's generational relationship to the principal (for example, we can estimate the birth decade of a father to be 2 or 3 before the birth of their child. This helps us to distinguish people who have the same name but different generations).  Dates are always translated into the Gregorian Calendar.  Place names are lightly normalized to eliminate spelling variations.  The *date notes* indicate how the date was derived.
4. Source material - the names, dates, places as they are in the source record, for reference.

### Usage

For detailed usage information, invoke with the help flag.


```sh
% ./Normalize -h
```
