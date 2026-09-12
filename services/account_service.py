from storage.account_storage import AccountDatabase

from cli.errors import (
    AccountError,
    RankDivisionError,
    AccountAlreadyExistsError,
    AccountCreationError,
    AccountDoesntExist,
    AccountDeletionError,
    AccountAttributeError,
    AccountModificationError,
    AccountModificationRepetitiveValueError,
)


class AccountService:
    def __init__(self, database_file: str):
        self._account = AccountDatabase(database_file)

    def account_attributes(self, player_id) -> list[str]:
        try:
            attr_content = self._account.get_attributes(player_id)

            if attr_content is None:
                return []
            return attr_content
        except KeyError:
            raise AccountDoesntExist(player_id=player_id)
        except Exception as e:
            raise AccountError(error=e) from e

# --------------------------------------------------------------------------- #

    def get_account(self, player_id, requested_cred) -> dict[str, str]:
        try:
            received = self._account.get_account(player_id, requested_cred)
        except KeyError as e:
            raise AccountAttributeError(player_id=player_id,
                                        attribute=e.args[0]) from e
        except Exception as e:
            raise AccountError(error=e) from e

        if not received:
            raise AccountDoesntExist(player_id=player_id)

        return received

    def create_account(self, player_id, current_season) -> None:
        try:
            added = self._account.add_account(player_id, current_season)
        except Exception as e:
            raise AccountCreationError(player_id=player_id, error=e) from e

        if not added:
            raise AccountAlreadyExistsError(player_id=player_id)

    def show_accounts(self) -> list[str]:
        try:
            result = self._account.display_accounts()
            return result
        except Exception as e:
            raise AccountError(error=e) from e

    def modify_account(self, player_id, attr, new_value) -> None:
        try:
            modified = self._account.edit_account(player_id, attr, new_value)
        except KeyError as e:
            raise AccountAttributeError(
                player_id=player_id, attribute=e.args[0])
        except Exception as e:
            raise AccountModificationError(player_id=player_id, error=e) from e

        if not modified:
            raise AccountModificationRepetitiveValueError(
                player_id=player_id,
                attribute=attr,
                replacement=new_value,
            )

    def modify_account_name(self, player_id, new_player_id):
        try:
            self._account.modify_name(player_id, new_player_id)
        except KeyError as e:
            raise AccountDoesntExist(player_id=e.args[0]) from e
        except ValueError as e:
            raise AccountAlreadyExistsError(player_id=new_player_id) from e
        except Exception as e:
            raise AccountModificationError(player_id=player_id, error=e) from e

    def update_accounts(self, current_season):
        try:
            updated, nonupdated = self._account.update_accounts(current_season)
            return updated, nonupdated
        except Exception as e:
            raise AccountError(error=e) from e

    def remove_account(self, player_id) -> None:
        try:
            removed = self._account.delete_account(player_id)
        except Exception as e:
            raise AccountDeletionError(player_id=player_id, error=e) from e

        if not removed:
            raise AccountDoesntExist(player_id=player_id)

    def wide_search(self, player_id) -> list[str]:
        try:
            search_results = self._account.wide_search(player_id)
            return search_results
        except Exception as e:
            raise AccountError(error=e) from e

    def account_exists(self, player_id) -> bool:
        try:
            return self._account.account_exists(player_id)
        except Exception as e:
            raise AccountError(error=e) from e

    def rank_title(self, player_division, player_tier) -> str:
        try:
            rank = self._account.rank_return(player_division, player_tier)
            return rank
        except ValueError:
            raise RankDivisionError
        except Exception as e:
            raise e from e

    def rank_comparison(self, player_division, player_tier) -> str:
        try:
            rank = self._account.rank_compare(player_division, player_tier)
            return rank
        except ValueError:
            raise RankDivisionError
        except Exception as e:
            raise e from e