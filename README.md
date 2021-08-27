# LitvakScripts

Python scripts I use for manipulating and analyzing data collected by the litvak.org team.

Note: My scripts read data (e.g. spreadsheets) that are copyrighted by [LitvakSIG, Inc.](https://www.litvaksig.org) Accessing their data requires an account on their web site, and use of their data is subject to their terms of service and copyrights.  At the time of this writing, they have a web page that describes permitted uses [here](https://donors.litvaksig.org/site/suwalki/data-info).

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

```sh
% ./DownloadSpreadsheets -h
usage: DownloadSpreadsheets [-h] [-u USERNAME] [-p PASSWORD] [-g GROUP] [-o OUTDIR] [-x] [-n] [files ...]

Download a set of spreadsheets from Litvaksig.org

positional arguments:
  files                 Files to download. If not specified, download all files in the group.

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Litvaksig.org account username. [Default: LITVAK_USERNAME environment variable]
  -p PASSWORD, --password PASSWORD
                        Litvaksig.org account password. [Default: LITVAK_PASSWORD environment variable]
  -g GROUP, --group GROUP
                        The name of the district you subscribe to. [Default: suwalki/sejny]
  -o OUTDIR, --outdir OUTDIR
                        The directory where the spreadsheets will be placed. [Default: ./output]
  -x, --overwrite       Overwrite existing files. [Default: false]
  -n, --dry-run         Identify the files, but do not download them. [Default: false]
```
