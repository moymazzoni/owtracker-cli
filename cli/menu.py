from services.account_service import AccountService

from cli.errors import (
    AccountAttributeInvalidValueError,
    AccountInaccessibleAttribute,
    AccountNoAttributesError,
    NoOptionsInMenuError,
    AccountDoesntExist,
    OutOfRangeError,
    IncorrectValue,
    AccountError,
)
from cli.cli_utils import (
    short_format_rank,
    copy_credentials,
    run_with_spinner,
    print_menu_parts,
    read_userinput,
    format_rank,
    cli_msg,
    is_quit,
)

from collections.abc import Callable
import sys

EDIT_SPACING: int = 16
QUIT_OPTIONS: list[str] = ['quit', 'q']
FORCE_QUIT: str = cli_msg(text='Returning to main menu...', msg_type='warning')
QUIT_MSG: str = cli_msg(text='User has requested to quit.', msg_type='warning')

NONEDITABLE_FIELDS: frozenset[str] = frozenset({
    'ranks', 'rank_history', 'imported_at', 'last_updated_at'
})  # Add custom menu for rank & rank history edits.


def menu_loop(config) -> None:
    service = AccountService(config.db_directory)
    stay_in_loop: bool = True
    menu_options: list = []
    menu_len = getattr(config, 'display_len')
    display_accounts_double_wide = getattr(config, 'display_accounts_double_wide')
    auto_update_ranks = getattr(config, 'auto_update_ranks')
    credential_get = getattr(config, 'credential_get')
    hide_emails = getattr(config, 'hide_emails')
    hide_passwords = getattr(config, 'hide_passwords')
    current_season = getattr(config, 'current_season')

    if auto_update_ranks:
        cmd_update_ranks(service, current_season)

    options_dict: dict[int, tuple[str, Callable[..., None]]] = {
        1: ('Get Account', lambda: cmd_get_account(
            service, menu_len, credential_get, hide_emails, hide_passwords)),
        2: ('Add Account', lambda: cmd_add_account(service, current_season)),
        3: ('View Accounts', lambda: cmd_display_accounts(
            service,menu_len,display_accounts_double_wide)),
        4: ('Edit account', lambda: cmd_edit_accounts(
            service, menu_len, hide_emails, hide_passwords)),
        5: ('Delete account', lambda: cmd_delete_account(service, menu_len)),
        6: ('Update Ranks', lambda: cmd_update_ranks(service, current_season)),
        7: ('Rank History', lambda: cmd_rank_history(service, menu_len)),
        8: ('Range Detection', lambda: cmd_range_detection(service, menu_len)),
        9: ('Quit Program', lambda: sys.exit(0)),
    }

    for func_label, _ in options_dict.values():
        menu_options.append(func_label)

    while stay_in_loop:
        try:
            if not len(menu_options):
                raise NoOptionsInMenuError

            print_menu_parts(
                top_text="OWTracker Menu",
                bottom_text="End Menu",
                menu_contents=menu_options,
                list_type="num",
                menu_len=menu_len,
                double_space=True,
            )

            user_response = read_userinput(
                prompt=cli_msg(
                    text="Select option: ",
                    msg_type="question",
                    quit_option=f"{len(options_dict)}",
                ),
                expected_type=int,
            )

            if isinstance(user_response, int):
                if user_response not in range(1, len(options_dict) + 1):
                    raise OutOfRangeError(value=user_response)

            if user_response in options_dict:
                _, func = options_dict[user_response]
                func()
        except NoOptionsInMenuError as e:
            print(cli_msg(text=str(e), msg_type='error'))
            sys.exit(1)
        except OutOfRangeError as e:
            print(cli_msg(text=str(e), msg_type='error'))


def cmd_get_account(service, menu_len, credential_ini, hide_emails, hide_passwords) -> None:
    player_id = read_userinput(prompt=cli_msg(
        text='Enter battletag/username: ',
        msg_type='question',
    ))
    if valid_exit_condition(player_id):
        return

    player_id = _wide_search(player_id, service, menu_len)
    if valid_exit_condition(player_id):
        return

    try:
        credentials_items: list[str] = []

        if credential_ini == 'ask':
            credential_ini = read_userinput(prompt=cli_msg(
                text='Which credentials would you like to copy? '
                     'Options: "all", "tag" or "username", "email", '
                     '"password", "ep" (email and password): ',
                msg_type='question'))
            if valid_exit_condition(credential_ini):
                return

        credentials_received = service.get_account(player_id, credential_ini)
        for key, value in credentials_received.items():
            if value in ['', None]:  # Can't use, so just raise.
                raise AccountAttributeInvalidValueError(
                    player_id=player_id, attribute=key)
            if key not in NONEDITABLE_FIELDS:
                if (key == 'email' and hide_emails or key ==
                        'password' and hide_passwords):
                    value = '*' * len(value)
                credentials_items.append(f'{key:{EDIT_SPACING}}: {value}')

        print_menu_parts(
            top_text=f'"{player_id}" Clipboard Credentials',
            bottom_text='Account End',
            menu_contents=credentials_items,
            list_type='num',
            menu_len=menu_len,
            double_space=False,
        )

        copy_credentials(credentials_received)
    except AccountError as e:
        print(cli_msg(text=str(e), msg_type='error'))


def cmd_add_account(service, current_season) -> None:
    player_id = read_userinput(prompt=cli_msg(
        text='Enter battletag/username: ',
        msg_type='question',
    ))
    if valid_exit_condition(player_id):
        return

    try:
        run_with_spinner(
            service.create_account,
            player_id,
            current_season,
            message=cli_msg(
                text=f'Fetching account: "{player_id}".',
                msg_type='load',
            ),
        )
    except AccountError as e:
        print(cli_msg(text=str(e), msg_type='error'))
    else:
        print(cli_msg(
            text=f'Account "{player_id}" was successfully added.',
            msg_type='ok',
        ))


def cmd_display_accounts(service, menu_len, display_accounts_double_wide) -> None:
    try:
        account_keys = service.show_accounts()

        result = []
        for account in account_keys:
            account_ranks = service.account_attributes(account)

            if not account_ranks['ranks'].items():
                raise AccountAttributeInvalidValueError(
                    player_id=account, attribute='ranks'
                )

            rank_status = []
            for _ in account_ranks['ranks']:
                rank_status = [
                    short_format_rank(account_ranks['ranks']['tank']),
                    short_format_rank(account_ranks['ranks']['damage']),
                    short_format_rank(account_ranks['ranks']['support']),
                    short_format_rank(account_ranks['ranks']['open']),
                ]
            result.append(f'{account:{19}}: {" ".join(rank_status)}')
    except AccountError as e:
        print(cli_msg(text=str(e), msg_type='error'))
    else:
        print_menu_parts(
            top_text=f'Accounts List ({len(account_keys)})',
            bottom_text='Account End',
            menu_contents=result,
            list_type='star',
            menu_len=menu_len,
            double_space=display_accounts_double_wide,
        )


def cmd_edit_accounts(service, menu_len, hide_emails, hide_passwords) -> None:
    player_id = read_userinput(prompt=cli_msg(
        text='Enter battletag/username: ',
        msg_type='question',
    ))
    if valid_exit_condition(player_id):
        return

    player_id = _wide_search(player_id, service, menu_len)
    if valid_exit_condition(player_id):
        return

    try:
        while True:
            attr_dict = service.account_attributes(player_id)
            if not attr_dict:
                raise AccountNoAttributesError(player_id=player_id)

            display_content: list = []
            for key, value in attr_dict.items():
                if key not in NONEDITABLE_FIELDS:
                    if (key == 'email' and hide_emails and value or key ==
                            'password' and hide_passwords and value):
                        value = '*' * len(value)
                    display_content.append(f'{key:{EDIT_SPACING}}: {value}')

            print_menu_parts(
                top_text=f'Edit Account: "{player_id}"',
                bottom_text='End Menu',
                menu_contents=display_content,
                list_type='star',
                menu_len=menu_len,
            )

            target_attr = read_userinput(
                prompt=cli_msg(
                    text='Enter attribute: ',
                    msg_type='question',
                ),
                whitelist=list(attr_dict),
                whitelist_error='Attribute given is not valid: ',
            )
            if valid_exit_condition(target_attr):
                return
            if target_attr in NONEDITABLE_FIELDS:
                raise AccountInaccessibleAttribute(attribute=target_attr)

            new_attribute = read_userinput(prompt=cli_msg(
                text='Enter new attribute data: ',
                msg_type='question'
            ))
            if valid_exit_condition(new_attribute):
                return
            if not _account_exists(player_id, service):
                raise AccountDoesntExist(player_id=player_id)

            else:
                if target_attr == 'player_id':
                    service.modify_account_name(player_id, new_attribute)
                    print(cli_msg(
                        text=f'Account attribute "{target_attr}" has been updated '
                             f'to "{new_attribute}".',
                        msg_type='ok',
                    ))
                    return
                else:
                    service.modify_account(player_id, target_attr, new_attribute)
                    print(cli_msg(
                        text=f'Account attribute "{target_attr}" has been updated '
                             f'to "{new_attribute}".',
                        msg_type='ok',
                    ))
    except AccountError as e:
        print(cli_msg(text=str(e), msg_type='error'))


def cmd_delete_account(service, menu_len) -> None:
    player_id = read_userinput(prompt=cli_msg(
        text='Enter battletag/username: ',
        msg_type='question'
    ))
    if valid_exit_condition(player_id):
        return

    player_id = _wide_search(player_id, service, menu_len)
    if valid_exit_condition(player_id):
        return

    try:
        if not _account_exists(player_id, service):
            raise AccountDoesntExist(player_id=player_id)

        confirm_delete = read_userinput(prompt=cli_msg(
            text=f'Are you certain you want to delete account "{player_id}"? '
                 f'(y/N): ',
            msg_type='warning',
        ))
        if confirm_delete.lower() == "y":
            service.remove_account(player_id)
        else:
            print(FORCE_QUIT)
            return
    except AccountError as e:
        print(cli_msg(text=str(e), msg_type='error'))
    else:
        print(cli_msg(
            text=f'Account "{player_id}" was successfully deleted.',
            msg_type='ok',
        ))


def cmd_update_ranks(service, current_season) -> None:
    try:
        updated, nonupdated = run_with_spinner(
            service.update_accounts,
            current_season,
            message=cli_msg(
                text=f'Fetching database account\'s newest ranks...',
                msg_type='load',
            ),
        )
    except AccountError as e:
        print(cli_msg(text=str(e), msg_type='error'))
    else:
        print(cli_msg(
            text=f'Accounts in database have been sifted through...',
            msg_type='ok',
        ))
        print(cli_msg(text=updated, msg_type='ok'))
        if nonupdated:
            print(cli_msg(text=nonupdated, msg_type='warning'))


def cmd_rank_history(service, menu_len) -> None:
    """
    Print out every season alongside the roles and ranks of the given account.
    """
    player_id = read_userinput(prompt=cli_msg(
        text='Enter battletag/username: ',
        msg_type='question'
    ))

    if valid_exit_condition(player_id):
        return

    player_id = _wide_search(player_id, service, menu_len)
    if valid_exit_condition(player_id):
        return

    try:
        account_information = service.account_attributes(player_id)

        if not account_information['rank_history']:
            raise AccountAttributeInvalidValueError(
                player_id=player_id, attribute='rank_history'
            )

        for season, roles in account_information['rank_history'].items():
            rank_status = [
                format_rank("tank", roles["tank"]),
                format_rank("damage", roles["damage"]),
                format_rank("support", roles["support"]),
                format_rank("open", roles["open"]),
            ]

            print_menu_parts(
                top_text=f"Season: {season}",
                bottom_text="End Season",
                menu_contents=rank_status,
                list_type="bullet",
                menu_len=menu_len,
                double_space=False,
            )
    except AccountError as e:
        print(cli_msg(text=str(e), msg_type='error'))
    return


def cmd_range_detection(service, menu_len) -> str | None:
    """
        Asks the user for two accounts and their roles (first account and first
        account role then second account and secound account role),
        does calculations to determine range, and print if they are in range
        or not.

        :raises ValueError: Invalid division #, cancelling the detection.
        :raises KeyError: Invalid tier, cancelling detection.
        :raises AttributeError: Invalid use of .lower(), meaning the returned type
            was most likely a ``None``, meaning an empty result (invalid).
        """
    try:
        player_id = read_userinput(prompt=cli_msg(
            text='Enter first battletag/username: ',
            msg_type='question'
        ))

        if valid_exit_condition(player_id):
            return

        player_id = _wide_search(player_id, service, menu_len)
        if valid_exit_condition(player_id):
            return

        if not _account_exists(player_id, service):
            raise AccountDoesntExist(player_id=player_id)

        given_role = read_userinput(cli_msg(
            text=f"{player_id}'s role? (tank, damage, support, open): ",
            msg_type="question",
        )).lower()

        if valid_exit_condition(given_role):
            return

        player1_data = service.account_attributes(player_id)
        player1_role = player1_data.get('ranks', {}).get(given_role, {})

        if player1_role is None:
            print(cli_msg(
                text=f'No rank data for role "{given_role}"',
                msg_type='error',
            ))
            return

        player1_division = player1_role.get('division', {})
        player1_tier = player1_role.get('tier', {})

        p1_rank = service.rank_title(player1_division, player1_tier)
        print(cli_msg(
            text=f"Selected rank: {short_format_rank(player1_role)} | {p1_rank}"
        ))

        player_id2 = read_userinput(prompt=cli_msg(
            text='Enter second battletag/username: ',
            msg_type='question'
        ))

        if valid_exit_condition(player_id2):
            return

        player_id2 = _wide_search(player_id2, service, menu_len)
        if valid_exit_condition(player_id2):
            return

        if not _account_exists(player_id2, service):
            raise AccountDoesntExist(player_id=player_id2)

        given_role2 = read_userinput(cli_msg(
            text=f"{player_id2}'s role? (tank, damage, support, open): ",
            msg_type="question",
        )).lower()

        if valid_exit_condition(given_role2):
            return

        player2_data = service.account_attributes(player_id2)
        player2_role = player2_data.get('ranks', {}).get(given_role2, {})

        if player2_role is None:
            print(cli_msg(
                text=f'No rank data for role "{given_role}"',
                msg_type='error',
            ))
            return

        player2_division = player2_role.get('division', {})
        player2_tier = player2_role.get('tier', {})

        p2_rank = service.rank_title(player2_division, player2_tier)
        print(cli_msg(
            text=f"Selected rank: {short_format_rank(player2_role)} | {p2_rank}"
        ))
        print(service.rank_comparison(p1_rank, p2_rank))
    except AccountDoesntExist as e:
        print(cli_msg(text=str(e), msg_type='error'))
    except (ValueError, KeyError, AttributeError) as e:
        print(cli_msg(text=str(e), msg_type='error'))

# --------------------------------------------------------------------------- #

def valid_exit_condition(string: str) -> bool:
    if is_quit(string):
        print(QUIT_MSG)
        return True
    if string in ['', None]:
        print(FORCE_QUIT)
        return True
    return False


def _wide_search(substring, service, menu_len) -> str | None:
    wide_search_results = service.wide_search(substring)

    if not wide_search_results:
        return substring
    # Only one item (exact match/closest, no contest).
    elif len(wide_search_results) < 2:
        return wide_search_results[0]

    print_menu_parts(
        top_text=f'Accounts with: "{substring}"',
        bottom_text='End of Options',
        menu_contents=wide_search_results,
        list_type='num',
        menu_len=menu_len
    )

    selection = read_userinput(
        prompt=cli_msg(text='Choose an account: ', msg_type='question'),
    )

    if not selection:
        return None
    if selection in QUIT_OPTIONS:
        return QUIT_OPTIONS[1]

    try:
        if selection.isdigit():
            selection = int(selection)

            if selection in range(1, len(wide_search_results) + 1):
                return wide_search_results[selection - 1]  # Index of item.
            else:
                raise OutOfRangeError(value=selection)
        else:
            raise IncorrectValue(value=selection)
    except OutOfRangeError as e:
        print(cli_msg(text=str(e), msg_type='error'))
    except IncorrectValue as e:
        print(cli_msg(text=str(e), msg_type='error'))

def _account_exists(player_id, service) -> bool:
    in_database = service.account_exists(player_id)

    if not in_database:
        return False
    return True