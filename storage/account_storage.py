from api_client import OverfastClient
from dataclasses import dataclass
from enum import Enum

import json
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class Tier(Enum):
    bronze = 0
    silver = 1
    gold = 2
    platinum = 3
    emerald = 4
    diamond = 5
    master = 6
    grandmaster = 7
    ultimate = 8

WIDE_THRESHOLD = {
    Tier.bronze: 5,
    Tier.silver: 5,
    Tier.gold: 5,
    Tier.platinum: 5,
    Tier.emerald: 5,
    Tier.diamond: 5,
    Tier.master: 4,
    Tier.grandmaster: 3,
    Tier.ultimate: 2,
}

@dataclass(frozen=True)
class Rank:
    tier: Tier  # bronze, silver, etc.
    division: int  # I, II, III, etc.

    def __post_init__(self):
        if not (1 <= self.division <= 5):
            raise ValueError

    def value(self) -> int:
        return self.tier.value * 5 + (5 - self.division)

    def __str__(self):
        return f"{self.tier.name.title()} {self.division}"


def divisions_apart(a: Rank, b: Rank) -> int:
    return abs(a.value() - b.value())


def is_wide_group(a: Rank, b: Rank) -> bool:
    higher = max(a, b, key=lambda r: r.value())
    threshold = WIDE_THRESHOLD[higher.tier]
    return divisions_apart(a, b) > threshold


def describe_group(a: Rank, b: Rank) -> str:
    gap = divisions_apart(a, b)
    status = "WIDE" if is_wide_group(a, b) else "in range"
    return f"{a} + {b}: {gap} division(s) apart → {status}"

def validate_email(email: str) -> None:
    if not EMAIL_RE.match(email):
        raise ValueError(f"Invalid email: {email!r}")

class AccountDatabase:
    def __init__(self, database_file: str):  # database file.
        self.database_file = database_file

    def _load(self) -> dict:
        with open(self.database_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self, data: dict) -> None:
        with open(self.database_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def wide_search(self, substring):
        account_keys = self.display_accounts()

        substring_matches: list = []
        for account in account_keys:
            if substring.lower() in account.lower():
                substring_matches.append(account)
        return substring_matches

    def account_exists(self, player_id):
        data = self._load()

        return player_id in data['accounts']

    def get_attributes(self, player_id):
        data = self._load()
        attribute_location: dict = data['accounts'][player_id]

        if attribute_location.values() is None:
            return None

        attr_dict = {'player_id': player_id}  # account tag.
        for attr, value in attribute_location.items():
            attr_dict[attr] = value
        return attr_dict

    def modify_name(self, player_id, new_player_id):
        data = self._load()

        if new_player_id in data['accounts']:
            raise ValueError

        data['accounts'][new_player_id] = data['accounts'][player_id]

        del data['accounts'][player_id]  # old player_id.

        self._save(data)

# --------------------------------------------------------------------------- #

    def get_account(self, player_id, requested_credentials) -> bool | list:
        data = self._load()

        if player_id not in data['accounts']:
            return False

        credential_info: dict[str, str] = {}
        requested_list = requested_credentials.split('+')

        for request in requested_list:
            match request:
                case 'tag' | 'username':
                    credential_info['username'] = player_id
                case 'email':
                    credential_info['email'] =\
                        data['accounts'][player_id]['email']
                case 'password':
                    credential_info['password'] =\
                        data['accounts'][player_id]['password']
                case 'ep':
                    credential_info['email'] =\
                        data['accounts'][player_id]['email']
                    credential_info['password'] =\
                        data['accounts'][player_id]['password']
                case 'all':
                    credential_info['username'] = player_id
                    credential_info['email'] =\
                        data['accounts'][player_id]['email']
                    credential_info['password'] =\
                        data['accounts'][player_id]['password']
                case _:
                    credential_info['username'] = player_id

        return credential_info


    def add_account(self, player_id, current_season):
        data = self._load()

        if player_id not in data['accounts']:
            client = OverfastClient()

            account_data = client.get_player_info(player_id)
            data.setdefault('accounts', {})[player_id] = account_data

            prev_season = client.get_known_last_season(player_id)
            if prev_season != current_season:
                prev_ranks = client.get_known_last_season_ranks(player_id)

                data['accounts'][player_id]['rank_history'] = {
                   str(prev_season) : prev_ranks
                }
                data['accounts'][player_id]['ranks'] = {
                    "tank": None,
                    "damage": None,
                    "support": None,
                    "open": None,
                }

            self._save(data)
            return True
        else:
            return False

    def display_accounts(self):
        data = self._load()
        return data['accounts'].keys()

    def edit_account(self, player_id, target_attr, new_attr) -> bool:
        data = self._load()

        if target_attr == 'email' and new_attr is not None:
            validate_email(new_attr)

        if data['accounts'][player_id][target_attr] == new_attr:
            return False
        else:
            data['accounts'][player_id][target_attr] = new_attr
            self._save(data)
            return True

    def delete_account(self, player_id):
        data = self._load()

        if player_id not in data['accounts']:
            return False
        del data['accounts'][player_id]
        self._save(data)
        return True

    def update_accounts(self, current_season):
        data = self._load()

        account_list = self.display_accounts()
        accounts_updated: list[str] = []
        accounts_failed_fetch: list[str] = []

        client = OverfastClient()

        empty_ranks = {
            "tank": None,
            "damage": None,
            "support": None,
            "open": None,
        }

        for account in account_list:
            try:
                updated_ranks = client.get_player_info(account)['ranks']
                fetched_season = client.get_known_last_season(account)
            except Exception:
                # covers a failed/slow player-info fetch AND a failed last-season lookup - account got no useable data,
                # so skip it without touching anything else already saved.
                accounts_failed_fetch.append(account)
                continue

            changed = False

            if fetched_season == current_season:
                # up-to-date ranks of current season.
                if data['accounts'][account]['ranks'] != updated_ranks:
                    data['accounts'][account]['ranks'] = updated_ranks
                    changed = True
            else:
                # outdated season. the fetch reflects the player's last active season. keep rank_history for that
                # season up to date with the freshest known data, and clear the current-season slot.
                season_key = str(fetched_season)

                if data['accounts'][account]['rank_history'].get(
                        season_key) != updated_ranks:
                    data['accounts'][account]['rank_history'][
                        season_key] = updated_ranks
                    changed = True

                if data['accounts'][account]['ranks'] != empty_ranks:
                    data['accounts'][account]['ranks'] = empty_ranks
                    changed = True

            if changed:
                accounts_updated.append(account)
                # Save as each account lands rather than at the end in case an account fetch error happens (so no time
                # is wasted).
                self._save(data)

        return (
            f'Accounts updated/changed: '
            f'{", ".join(accounts_updated) or None}.',
            f'Accounts not fetched properly'
            f'{' (private, banned, or not a real account): ' 
            if accounts_failed_fetch else ': '}'
            f'{", ".join(accounts_failed_fetch) or None}.',
        )

    @staticmethod
    def rank_return(player_division, player_tier):
        return Rank(Tier[player_division.lower()], player_tier)

    @staticmethod
    def rank_compare(player1, player2):
        return describe_group(player1, player2)