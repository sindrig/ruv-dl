Sync available ruv programs to your computer

Build: [![CircleCI](https://circleci.com/gh/sindrig/ruv-dl.svg?style=svg)](https://circleci.com/gh/sindrig/ruv-dl)

# Installation

`pip install ruv-dl`

# Usage

See `ruv-dl --help`

# Development

1. Clone this repo
2. Create and activate a virtual environment (install tox or rely on system
wide installation)
3. `cd $PATH_TO_RUV_DL`
4. `pip install -e ./`
5. Run the tests: `tox`

# Crontab

Ruv-dl works best when it's being run periodically in cron. Start by running
it manually and start downloading some programs, e.g.
`ruv-dl download Hvolpasveitin`. Now that program is considered to be synced.
After that you can run `ruv-dl download -u` and it will attempt to download
new episodes in previously synced programs.

# Configuration

All configuration is done via command-line arguments. The one you're most
likely to want to change is the `--destination` flag.

    ruv-dl --destination /media/TV download -u

# Migrations

No data migrations will be run unless you explicitly call them, and the program
might exit abruptly if it senses a missing migration. Make sure to call the
`migrate` command with the same parameters as you would call the `download`
command.

    ruv-dl --destination /media/TV migrate 1

Note that some migrations expect you to have already attempted a download,
so do not run migrations unless the program tells you to.

# Uploading a new version

1. Set a new version in setup.py
2. Run `. ./prepare_upload.sh` (this is assuming you have lastpass.
    Optional if you want to type your pypi credentials manually).
3. Run `make pypi`