from ow_season_scraper import gather_data

from dataclasses import dataclass
from pathlib import Path
import configparser
import json
import sys
import re

BASE_DIR = Path(__file__).parent
SETTINGS_FILE = BASE_DIR / 'settings.ini'  # Should always be there.
VALID_TOKENS = {"username", "tag", "email", "password"}

DEFAULT_SETTINGS = {
    'General': {
        'username': 'User',
        'display_len': '84',
        'display_accounts_double_wide': 'True',
        'auto_update_ranks': 'False',
        'hide_emails': 'False',
        'hide_passwords': 'True',
        'credential_get': 'email+password',
        'delete_warning_prompt': 'True',
    },
    'Paths': {
        'database': str(BASE_DIR / 'storage' / 'accounts.json'),
    },
}

DEFAULT_ACCOUNTS = {
    'accounts': {
    },
}

REQUIRED = {
    'General': {'username': str,
                'display_len': int,
                'display_accounts_double_wide': bool,
                'auto_update_ranks': bool,
                'hide_emails': bool,
                'hide_passwords': bool,
                'credential_get': str,
                'delete_warning_prompt': bool,
    },
    'Paths':   {'database': str},
}

@dataclass(frozen=True)
class AppConfig:
    username: str
    display_len: int
    display_accounts_double_wide: bool
    auto_update_ranks: bool
    hide_emails: bool
    hide_passwords: bool
    credential_get: str
    delete_warning_prompt: bool
    current_season: int | None
    season_title: str | None
    latest_patch_date: str | None
    db_directory: str


def is_valid_format(s: str) -> bool:
    if s == "all" or "ask":
        return True

    parts = s.split("+")

    # only valid tokens.
    if not all(re.fullmatch(r'ask|username|tag|email|password', p) for p in
               parts):
        return False

    # set removes dupes.
    if len(parts) != len(set(parts)):
        return False

    # can't have both (same purpose/use).
    if "username" in parts and "tag" in parts:
        return False

    # "all" has to be standalone.
    if ["all", "ask"] in parts:
        return False

    return True


def verify_settings(config_data: configparser.ConfigParser) -> None:
    errors: list[str] = []

    for section, options in REQUIRED.items():
        if not config_data.has_section(section):
            errors.append(f"Missing section: [{section}]")
            continue
        for opt, typ in options.items():
            if not config_data.has_option(section, opt):
                errors.append(f"Missing option: {section}.{opt}")
                continue
            elif not config_data.get(section, opt).strip():
                errors.append(f"Missing option: {section}.{opt}")

            if opt == 'credential_get':
                try:
                    if not is_valid_format(config_data['General']['credential_get']):
                        raise ValueError
                except ValueError:
                    errors.append(
                        f'{section}.{opt} must follow strict guidelines for '
                        f'proper use: "all" or a combination with use of "+" '
                        f'in between: "username" (or) "tag", "email", or '
                        f'"password". Example: "username+password".')
            if opt == 'display_len':
                min_len: int = 38
                try:
                    value = int(config_data['General']['display_len'])

                    if not min_len <= value:
                        raise ValueError
                except ValueError:
                    errors.append(
                        f'{section}.{opt} must follow loose guidelines for '
                        f'proper use: value must be {min_len} or greater. '
                        f'Anything smaller than {min_len} makes reading '
                        f'entries significantly harder (text cutoff).')

            if typ is int:
                try:
                    config_data.getint(section, opt)
                except ValueError:
                    errors.append(f"{section}.{opt} must be an int, got "
                                  f"{config_data.get(section, opt)!r}")
            if typ is bool:
                try:
                    config_data.getboolean(section, opt)
                except ValueError:
                    errors.append(f"{section}.{opt} must be a bool, got "
                                  f"{config_data.get(section, opt)!r}")

    if errors:
        print('!> ERROR: Invalid config data:\n ⤷ ' + '\n ⤷ '.join(errors))
        ask_to_default_settings(config_data)
        errors_after_reset: list[str] = []
        for section, options in REQUIRED.items():
            if not config_data.has_section(section):
                errors_after_reset.append(f"Missing section: [{section}]")
                continue
            for opt, typ in options.items():
                if not config_data.has_option(section, opt):
                    errors_after_reset.append(f"Missing option: {section}.{opt}")
                continue
        if errors_after_reset:
            print('!> FATAL: Defaults themselves are invalid:\n ⤷ ' +
                  '\n ⤷ '.join(errors_after_reset))
            sys.exit(1)


def verify_database(config_data: configparser.ConfigParser) -> None:
    try:
        db_file = config_data.get('Paths', 'database')
        with open(db_file, 'r') as file:
            data = json.load(file)
        if isinstance(data, dict) and 'accounts' in data:
            return
        raise ValueError("!> ERROR: Database missing 'accounts' key.")
    except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
        print(f'!> ERROR: Invalid database use: {e}')
        ask_to_default_database(config_data)


def ask_to_default_database(config_data: configparser.ConfigParser) -> None:
    try:
        choice: str = input('!> WARNING: Reset database to defaults? '
                            'This erases its current contents. (y/N): ')
    except EOFError:
        choice = "n"
    if choice.strip().lower() != "y":
        print('> Exiting so you can inspect and correct manually '
              'before running the program again.')
        sys.exit(1)
    print('!> WARNING: Resetting database to factory defaults.')
    write_default_to_database(config_data)


def ask_to_default_settings(config_data: configparser.ConfigParser) -> None:
    try:
        choice: str = input('!> WARNING: Reset "settings.ini" to defaults? '
                            'This erases its current contents. (y/N): ')
    except EOFError:
        choice = "n"
    if choice.strip().lower() != "y":
        print('> Exiting so you can inspect and correct manually '
              'before running the program again.')
        sys.exit(1)
    print('!> WARNING: Resetting "settings.ini" to factory defaults.')
    write_default_to_settings(config_data)


def write_changes(given_data: configparser.ConfigParser) -> None:
    """ Write config data to disk. """
    with open(SETTINGS_FILE, 'w') as configfile:
        given_data.write(configfile)


def write_default_to_database(config_data: configparser.ConfigParser) -> None:
    try:
        db_file = config_data.get('Paths', 'database')
        Path(db_file).parent.mkdir(parents=True, exist_ok=True)
        with open(db_file, 'w') as f:
            json.dump(DEFAULT_ACCOUNTS, f, indent=4)
        write_changes(config_data)
    except OSError as e:
        print(f'!> ERROR: Could not create database file: {e}. Terminating.')
        sys.exit(1)


def write_default_to_settings(config_data: configparser.ConfigParser) -> None:
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        for section in config_data.sections():  # clear everything first
            config_data.remove_section(section)
        config_data.read_dict(DEFAULT_SETTINGS)  # then load clean defaults
        write_changes(config_data)
    except OSError as e:
        print(f'!> ERROR: Could not create settings file: {e}. Terminating.')
        sys.exit(1)


def load_config() -> configparser.ConfigParser:
    config_data = configparser.ConfigParser()

    if not SETTINGS_FILE.exists():
        print('!> ERROR: Config file was not found, creating a new one.')
        write_default_to_settings(config_data)
        write_changes(config_data)
    else:
        try:
            config_data.read(SETTINGS_FILE, encoding="utf-8")
        except (configparser.Error, UnicodeDecodeError, OSError):
            print(f'!> ERROR: Config file corrupt or unreadable '
                  f'(improper format).')
            ask_to_default_settings(config_data)

    return config_data


def init() -> AppConfig:
    config = load_config()

    verify_settings(config)
    verify_database(config)

    _general = config['General']
    _paths = config['Paths']

    username = _general.get('username')
    display_len = _general.getint('display_len')
    display_accounts_double_wide = _general.getboolean('display_accounts_double_wide')
    auto_update_ranks = _general.getboolean('auto_update_ranks')
    hide_emails = _general.getboolean('hide_emails')
    hide_passwords = _general.getboolean('hide_passwords')
    credential_get = _general.get('credential_get')
    delete_warning_prompt = _general.get('delete_warning_prompt')

    try:
        current_season, season_title, latest_patch_date = gather_data()
        current_season += 20  # Overwatch before rebrand (20).
    except Exception as e:
        print(f'!> WARNING: Could not fetch current season information: {e}')
        try:
            cache_path = BASE_DIR / 'storage' /'ow_season_cache.json'
            with open(cache_path, 'r', encoding='utf-8') as file:
                cached = json.load(file)

            if cached.get('stale'):
                print('!> WARNING: Cached data is marked stale.')

            current_season = cached.get('season')
            if current_season is not None:
                current_season += 20  # Overwatch before rebrand (20).
            season_title = cached.get('season_title')
            latest_patch_date = cached.get('latest_patch_date')
            print(f'> Falling back to cached data from '
                  f'{cached.get("scraped_at_utc", "unknown time")}.')
        except (OSError, json.JSONDecodeError) as cache_err:
            print(f'!> WARNING: Cache also unavailable: {cache_err}')
            current_season = None
            season_title = None
            latest_patch_date = None

    return AppConfig(
        username=username,
        display_len=display_len,
        display_accounts_double_wide=display_accounts_double_wide,
        auto_update_ranks=auto_update_ranks,
        hide_emails=hide_emails,
        hide_passwords=hide_passwords,
        credential_get=credential_get,
        delete_warning_prompt=delete_warning_prompt,
        current_season=current_season,
        season_title=season_title,
        latest_patch_date=latest_patch_date,
        db_directory=_paths['database'],
    )