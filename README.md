# OWTracker CLI

A small command-line interface (CLI) tool for keeping track of Overwatch accounts.
Account logins, current ranks, rank history, and more are tracked here. Easy-to-use 
commands to help the user manage multiple accounts and keep track of their ranks in
order to quickly start queueing with friends.

Ranks and season data come live from the community-run [OverFast API](https://github.com/TeKrop/overfast-api); 
everything else (logins, notes) is stored locally on your own machine.

## Features

- **Get Account**† — look up a saved account (by full or partial battletag)
  and copy its username, email, password, all of the above, or ask for 
  which items to copy to your clipboard.
- **Add Account** — pull an account's live info from the OverFast API and
  save it. If the account hasn't placed yet this season, its last-known
  ranks are saved to Rank History instead of showing as its current rank.
- **View Accounts**† — a compact, color-coded list of every saved account and
  its current rank in each role (tank, damage, support, open).
- **Edit account**† — update any stored field (email, password, notes,
  battletag, etc.).
- **Delete account**† — remove an account. Confirmation prompt is on by
  default; toggle it off in `settings.ini` if prefered.
- **Update Ranks**\*† — refresh every saved account's ranks in one go, and
  optionally do this automatically every time you start the program.
- **Rank History** — see what an account's ranks looked like in previous
  seasons it participated in.
- **Range Detection** — check whether two accounts' ranks are close enough
  to duo queue together without being a "wide" (restricted) group.

**Fuzzy search everywhere:** any menu option that asks for a battletag will
accept a partial match — type part of a name and OWTracker shows you every
saved account containing it to pick from.

\*Account ranks fetched from OverFast API are cached, so wait some time if
the fetched rank isn't the latest data and run **Update Ranks** once more.

†Values can be modified in `settings.ini` at any time. Restart the program
to apply these changes. 

## Requirements

- Python (see `pyproject.toml` for the current minimum version)
- Dependencies: `requests`, `beautifulsoup4`, `pyperclip`, `pynput`,
  `urllib3` (all installed for you below)

## Setup

```bash
git clone https://github.com/moymazzoni/owtracker-cli.git
cd owtracker-cli

# using uv (recommended — a uv.lock is included):
uv sync

# or with plain pip:
pip install -r <(python -c "import tomllib;print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))")
```

Then just run it:

```bash
uv run main.py
# or
python main.py
```

### Running it from anywhere (optional)

If you'd rather just type `owtracker` from any terminal instead of `cd`-ing
into the folder every time, run the included setup script once:

```bash
./install.sh
```

This installs a small `owtracker` command to `~/.local/bin` that points back at this exact clone, so `git pull`-ing 
updates works. If `~/.local/bin` isn't already on your PATH, the script tells you the one line to add for your shell.

You don't need to manually create any config files. On the program's first
launch, OWTracker writes a default `settings.ini` for you automatically, and 
will offer to create an empty `storage/accounts.json` the first time it looks
for your account database. `settings.example.ini` and
`storage/accounts.example.json` are there if you'd rather copy and
hand-edit them before your first run. You can safely delete them.

## Configuration (`settings.ini`)

| Option                         | Section | Meaning                                                                                                                                                                      |
|--------------------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `username`                     | General | Just a display label for you; not used for anything functional at the moment.                                                                                                |
| `display_len`                  | General | Width (in characters) of the menu boxes. Minimum value is 38.                                                                                                                |
| `display_accounts_double_wide` | General | Show the account list in two columns instead of one.                                                                                                                         |
| `auto_update_ranks`            | General | Run "Update Ranks" automatically every time the program starts.                                                                                                              |
| `hide_emails`                  | General | Mask emails on-screen with `*` (they're still copied to clipboard in full).                                                                                                  |
| `hide_passwords`               | General | Same, but for passwords.                                                                                                                                                     |
| `credential_get`               | General | What "Get Account" copies by default: `all`, `ask` (prompt every time), or any combination of `username`/`tag`, `email`, `password` joined with `+` (e.g. `email+password`). |
| `delete_warning_prompt`        | General | Whether "Delete account" asks you to confirm (`True`) or deletes immediately (`False`).                                                                                      |
| `database`                     | Paths   | Path to your accounts JSON file.                                                                                                                                             |

## About Your Data

`storage/accounts.json` stores account emails and passwords **in plain
text** on your own disk. I do not have access to your data at all.
`hide_emails`/`hide_passwords` only mask what's *printed to your terminal*
— they don't encrypt anything at rest. Treat that file like a password 
manager export: don't commit it, don't sync it to a public place, and 
don't share it around. The included `.gitignore` already keeps it 
(and your personal `settings.ini`) out of git.

## Limitations

As mentioned in a footnote earlier, the account rank storage system fetches from OverFast API which caches its data, 
so some data on a fetch right after a rankup might not occur on time. In that case, wait a while (10+ minutes) and 
attempt the command again (**Update Ranks**).

Current functionality of the copy credentials (**Get Account**) waits for the user to specifically press and release 
"Ctrl + V" for pasting the requested/queued data — meaning the user must let go of "Ctrl" in order to queue the next 
item successfully.

## Credits

Rank and player data provided by
[OverFast API](https://github.com/TeKrop/overfast-api) by TeKrop. Current
season/patch info is scraped directly from Blizzard's public patch notes
page; this project doesn't use any official Blizzard API.
