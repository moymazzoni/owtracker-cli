from cli.cli_colors import Color

from itertools import zip_longest
from pynput import keyboard
from typing import Any
import pyperclip
import threading
import itertools
import time
import sys
import re

QUIT_OPTIONS: list[str] = ['quit', 'q']
RANK_TO_COLOR_CONVERSION: dict[str, str] = {
    "bronze": Color.BRONZE_BG,
    "silver": Color.SILVER_BG,
    "gold": Color.GOLD_BG,
    "platinum": Color.PLATINUM_BG,
    "emerald": Color.EMERALD_BG,
    "diamond": Color.DIAMOND_BG,
    "master": Color.MASTER_BG,
    "grandmaster": Color.GRANDMASTER_BG,
    "ultimate": Color.CHAMPION_BG
}

def _visible_len(s: str) -> int:
    """
    Length of ```s``` as it appears on screen, ignoring ANSI escape codes.
    """
    _ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
    return len(_ANSI_RE.sub('', s))


def _spinner(
    stop_event,
    message="...",
    status: dict | None = None
) -> None:
    """
    Display a spinner animation in the terminal until stopped.

    :param stop_event: A threading. Event that halts the spinner when set.
    :param message: Text displayed alongside the spinner frames.
    :param status: Shared dict with an "ok" bool, set by the caller before
        ``stop_event`` is set. Determines whether the final glyph is a
        checkmark (success) or an x (exception/interrupt).
    """
    frames = itertools.cycle("|/—\\")

    while not stop_event.is_set():
        sys.stdout.write(f"\r{message} {next(frames)}")
        sys.stdout.flush()
        time.sleep(0.2)

    ok = status.get("ok", True) if status else True
    glyph = (
        f"{Color.GREEN}{Color.UNDERLINE}✓{Color.END}"
        if ok else
        f"{Color.RED}{Color.UNDERLINE}✗{Color.END}"
    )

    sys.stdout.write(f"\r{message} {glyph}\n")
    sys.stdout.flush()


def cli_msg(text,
            msg_type: str = '',
            quit_option: str = str(QUIT_OPTIONS[1]).upper()
    ) -> str:
    """
    Changes the diplayed ``text`` message based on the ``msg_type`` given. If
    none are given, it will diplay the message as: ">> [text]" with no color
    modifier.

    :param text: The string that is passed in to be altered.
    :param msg_type: The type of color and glyphs to be applied to the ``text``.
    :param quit_option: If not ``None``, it will use the given string.
    :return: The modified ``text``, a string.
    """
    color: str = ''
    glyphs: str = '-→'

    if msg_type.lower() in ["success", "ok"]:  # Success message.
        color = Color.GREEN
        glyphs = '>>'
    if msg_type.lower() in ["question", "?"]:  # Same line ask for user I/O.
        quit_button =\
            (quit_option.upper() if quit_option == "" else quit_option)
        text = f'({quit_button}) {text}'
    if msg_type.lower() in ['warning', '!!']:
        color = Color.YELLOW
        text = f'WARNING: {text}'
        glyphs = '?>'
    if msg_type.lower() in ['error', '!']:
        color = Color.RED
        text = f'ERROR: {text}'
        glyphs = '!>'
    if msg_type.lower() in ['spinner', 'load']:
        glyphs='⤷'

    return f'{color}{glyphs} {text}{Color.END}'


def run_with_spinner(func, *args, message="Running", **kwargs) -> Any:
    """
    Run a function with a spinner animation playing in a background thread.

    :param func: The function to execute.
    :param args: Positional arguments passed to func.
    :param message: Text displayed alongside the spinner.
    :param kwargs: Keyword arguments passed to func.
    :returns: The return value of func.
    """
    stop_event = threading.Event()
    status = {"ok": True}
    thread = threading.Thread(
        target=_spinner,
        args=(stop_event, message, status),
        daemon=True,
    )

    thread.start()

    try:
        return func(*args, **kwargs)
    except BaseException:
        status["ok"] = False
        raise
    finally:
        stop_event.set()
        thread.join()


def print_menu_parts(
    top_text: str = "",
    bottom_text: str = "",
    menu_contents: list[str] | None = None,
    list_type: str | None = None,
    menu_len: int = 64,
    double_space: bool = False,
) -> None:
    """
    Print a bordered menu block with a header, content, and footer.

    :param top_text: Label displayed in the top border.
    :param bottom_text: Label displayed in the bottom border.
    :param menu_contents: Items to display. Defaults to an empty message.
    :param list_type: ``"num"`` for numbered, ``"bullet"`` for bullets,
        or ``None`` for plain.
    :param menu_len: Horizontal length of the menu window.
    :param double_space: True for double column ``menu_content`` display or
        False for single column display.
    """

    tleft: str = '╭──'
    tright: str = '──╮'
    bleft: str = '╰──'
    bright: str = '──╯'

    _ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

    def typogrpahic_emphasis(text: str, underline: bool = False):
        u = f'{Color.UNDERLINE}'
        return f'{Color.BOLD}{u if underline else ""}{text}{Color.END}'

    def center_dividers_and_space(text: str, text_pos: str = 'top'):
        if text_pos == 'bottom':
            left = bleft
            right = bright
        else:
            left = tleft
            right = tright

        center_msg_len = menu_len - len(tleft) - len(tright) - 2

        # pad based on visible length, not raw len() (which counts ANSI codes).
        visible = _visible_len(text)
        total_padding = max(center_msg_len - visible, 0)
        left_pad = total_padding // 2
        right_pad = total_padding - left_pad

        return f'{left} {" " * left_pad}{text}{" " * right_pad} {right}'

    top_text = typogrpahic_emphasis(top_text, underline=True)
    top_text = center_dividers_and_space(top_text)
    bottom_text = typogrpahic_emphasis(bottom_text, underline=False)
    bottom_text = center_dividers_and_space(bottom_text, 'bottom')

    def _pad_visible(s: str, width: int) -> str:
        """
        Pad ``s`` with trailing spaces so its *visible* length reaches ``width``,
        ignoring ANSI escape codes when measuring.
        """
        pad_len = max(width - _visible_len(s), 0)
        return f'{s}{" " * pad_len}'

    def _truncate_visible(s: str, visible_width: int) -> str:
        """
        Truncate ``s`` to ``visible_width`` *visible* characters, copying any
        ANSI escape sequences through untouched (without counting them
        toward the width) so colors aren't cut mid-code.
        """
        result_chars: list[str] = []
        visible_count = 0
        i = 0
        while i < len(s) and visible_count < visible_width:
            match = _ANSI_RE.match(s, i)
            if match:
                result_chars.append(match.group())
                i = match.end()
                continue
            result_chars.append(s[i])
            visible_count += 1
            i += 1
        return ''.join(result_chars)

    def build_menu_labels(content, glyph_name: str = '') -> list[str]:
        glyph: str = ''
        match glyph_name:
            case 'num':
                glyph = None
            case 'bullet':
                glyph = '•'
            case 'arrow':
                glyph = '-→'
            case 'curve arrow':
                glyph = '↪'
            case 'star':
                glyph = '⊹'
            case _:
                glyph = ' '

        return [
            f'{glyph if glyph else f"{i}."} {element}'
            for i, element in enumerate(content, start=1)
        ]

    def is_long(item: str):
        visible = _visible_len(item)
        if double_space and visible > (menu_len // 2) - 2:
            #  "- 5" because of the space at the start & the ellipsis
            #  replacing the end of the label.
            item = _truncate_visible(item, (menu_len // 2) - 5) + Color.END + '...'
        elif not double_space and visible > menu_len:
            item = _truncate_visible(item, menu_len - 3) + Color.END + '...'
        return item

    def print_single_column(labels: list[str]) -> None:
        if not labels:  # In case nothing was in the list.
            line = f'{"(Empty.)":^{menu_len}}'
            print(line)
        else:
            for item in labels:
                print(is_long(item))

    def print_two_column(labels: list[str], col_width: int = 32) -> None:
        """
        Print ``labels`` split into left/right columns, left-padded to
        ``col_width`` visible characters before the separator.
        """
        if not labels:  # Nothing was in the list.
            line = f'{"(Empty.)":^{menu_len}}'
            print(line)
        else:
            mid = (len(labels) + 1) // 2  # left column gets extra item if odd
            left_col = labels[:mid]
            right_col = labels[mid:]

            for left, right in zip_longest(left_col, right_col, fillvalue=""):
                left = is_long(left)
                right = is_long(right)
                line = f'{_pad_visible(left, col_width)}| {right}'
                print(line)

    labels_list = build_menu_labels(menu_contents, list_type)

    print(top_text)
    if double_space:
        print_two_column(labels_list, col_width=menu_len // 2)
    else:
        print_single_column(labels_list)
    print(bottom_text)


def read_userinput(
    prompt: str,
    expected_type: type = str,
    whitelist: list[Any] = None,
    whitelist_error: str = "Cannot use given: ",
) -> Any:
    """
    Prompt the user for input, then validate the type (default is str).
    Afterward, go through a whitelist check if given and print either a
    default error message or a custom one given.

    :param prompt: Text displayed to the user before input.
    :param expected_type: Type to cast the raw input to.
    :param whitelist: Collection of allowed values.
    :param whitelist_error: Message prefix printed on a non-whitelist attempt.
    :returns: The cast value on success or ``None`` for the following: an
        unexpected type, non-whitelist item found, or user quit.
    """
    raw_response: str = input(prompt).strip()

    try:
        user_response: str = expected_type(raw_response)
    except ValueError:
        print(cli_msg(
            text = f"Incorrect type, expected: {expected_type.__name__}.",
            msg_type="error",
            )
        )
        return None

    if whitelist:
        if is_quit(user_response):
            return 'q'
        if user_response in ['', None]:
            return ''
        if user_response not in whitelist:
            print(cli_msg(
                text=f'{whitelist_error}"{user_response}".',
                msg_type="error",
            ))
            return None

    return user_response

def copy_credentials(credentials_to_copy) -> None:
    """
    Goes through the tuple of items which correlate with keywords. If
    the keywords are present, the user will copy that item.
    """
    items = credentials_to_copy
    try:
        for label, value in items.items():
            if not value:
                continue
            pyperclip.copy(value)
            print(cli_msg(
                text=f"{label.capitalize()} copied. Waiting for Ctrl+V...",
                msg_type="success",
            ))
            _wait_for_paste_shortcut()
    finally:
        pyperclip.copy("")  # In case of interrupt, forces the copying of air.


def _wait_for_paste_shortcut() -> None:
    """ Blocks until Ctrl+V is pressed. """
    done: bool = False

    def on_activate() -> None:
        nonlocal done
        done = True

    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<ctrl>+v'),
        on_activate,
    )

    def on_press(key):
        hotkey.press(listener.canonical(key))

    def on_release(key):
        hotkey.release(listener.canonical(key))

    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release
    ) as listener:
        while not done:
            listener.join(timeout=0.1)
            if not listener.is_alive():
                break


def format_rank(role: str, rank_data: dict[str, str] | None) -> str:
    """
    Formats an accounts rank with a color code and division number to display.
    The color is representative of the tier color in-game.

    Example:
        Echo#1776
        * tank : (color)
        * damg : (color)
        * supp : (color)
        * open : (color)

    :param role: Account's competitive role name (such as "support").
    :param rank_data: The rank/tier and division of that role.
    :return: Formatted, color-coded rank string.
    """
    if not rank_data:  # If no rank data.
        return f"{role:<9}: n/a"  # We know there is no tier if no rank.

    rank_color: str | None = (
        RANK_TO_COLOR_CONVERSION.get(rank_data["division"])
    )

    return (
        f"{role:<9}: "
        f"{rank_color}{Color.BLACK} "
        f"{rank_data["tier"]} "
        f"{Color.END}"
    )

def short_format_rank(rank_data: dict[str, str] | None) -> str:
    if not rank_data:  # If no rank data.
        return f"n/a"  # We know there is no tier if no rank.

    rank_color: str | None = (
        RANK_TO_COLOR_CONVERSION.get(rank_data["division"])
    )

    return f"{rank_color} {Color.BLACK}{rank_data["tier"]} {Color.END}"

def is_quit(user_input) -> bool:
    """
    Easy check if the input from the user is None or a quit option.

    :param user_input: The string used to evaluate criteria conditions.
    :returns: ``True`` if it meets the criteria, ``False`` if it doesn't.
    """
    if user_input in QUIT_OPTIONS:
        return True
    return False