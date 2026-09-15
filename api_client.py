from __future__ import annotations
import time
import requests


class OverfastAPIError(Exception):
    pass


class PlayerNotFoundError(OverfastAPIError):
    pass


class RateLimitError(OverfastAPIError):
    pass


class OverfastConnectionError(OverfastAPIError):
    pass


class OverfastClient:
    BASE_URL = 'https://overfast-api.tekrop.fr'

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f'{self.BASE_URL}{path}'
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
        except requests.exceptions.Timeout as e:
            raise OverfastConnectionError(
                f'Request to OverFast API timed out | {e}') from e
        except requests.exceptions.ConnectionError as e:
            raise OverfastConnectionError(
                f'Could not connect to OverFast API | {e}') from e

        if response.status_code == 404:
            raise PlayerNotFoundError(
                'Player not found | private profile or incorrect battletag.')
        if response.status_code == 429:
            raise RateLimitError(
                'API rate limit reached | chill with the requests.')
        if response.status_code >= 400:
            raise OverfastAPIError(f'OverFast API error '
                                   f'{response.status_code}: {response.text}.')

        return response.json()

    @staticmethod
    def _clean_rank(rank: dict | None) -> dict | None:
        """
        Strips icon URLs (role_icon, rank_icon, tier_icon) from a rank entry.
        """
        if rank is None:
            return None
        return {k: v for k, v in rank.items() if k not in
                {'role_icon', 'rank_icon', 'tier_icon'}}

    def get_player_summary(self, player_id: str) -> dict:
        """
        Fetches the full summary profile for a player from the OverFast API.

        Battletags with ``#`` (e.g. ``Player#1234``) are normalized
        automatically to the hyphenated form the API expects (``Player-1234``).

        :param player_id: The player's battletag (e.g. ``Player#1234``).
        :returns: Raw summary payload from the OverFast API.
        :raises PlayerNotFoundError: If the battletag doesn't exist or the
            profile is private.
        :raises RateLimitError: If the API rate limit has been hit.
        """
        normalized_id = player_id.replace('#', '-')
        return self._get(f'/players/{normalized_id}/summary')

    def get_known_last_season(self, player_id: str) -> int:
        """
        Returns the season number of the account's last competitive season
        played (must have been placed).
        """
        normalized_id = player_id.replace('#', '-')
        data = self._get(f'/players/{normalized_id}')
        return data["summary"]["competitive"]["pc"]["season"]

    def get_known_last_season_ranks(self, player_id: str) -> dict:
        normalized_id = player_id.replace('#', '-')
        data = self._get(f'/players/{normalized_id}')
        ranks = data["summary"]["competitive"]["pc"]

        return {
            'tank': self._clean_rank(ranks.get('tank')),
            'damage': self._clean_rank(ranks.get('damage')),
            'support': self._clean_rank(ranks.get('support')),
            'open': self._clean_rank(ranks.get('open')),
        }

    def get_player_info(self, player_id: str) -> dict:
        """
        Returns a trimmed-down account record: username, current competitive
        ranks (PC), when this record was pulled, and when the API last
        updated the underlying data.
        """
        summary = self.get_player_summary(player_id)
        ranks = (summary.get('competitive') or {}).get('pc') or {}

        return {
            'username': summary.get('username'),
            'email': None,
            'password': None,
            'ranks': {
                'tank': self._clean_rank(ranks.get('tank')),
                'damage': self._clean_rank(ranks.get('damage')),
                'support': self._clean_rank(ranks.get('support')),
                'open': self._clean_rank(ranks.get('open')),
            },
            'rank_history': {},
            'notes': None,
            'imported_at': int(time.time()),
            'last_updated_at': summary.get('last_updated_at'),
        }
