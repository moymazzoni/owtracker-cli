# / Used for the terminal to display color, bold, italic,
# \ and other forms of text.
# Credit to: https://stackoverflow.com/a/17303428
class Color:
    GREEN = '\x1b[38;2;80;220;100m'
    YELLOW = '\x1b[38;2;230;200;60m'
    RED = '\x1b[38;2;247;84;100m'

    # Overwatch rank colors.
    BRONZE = "\x1b[38;2;204;120;81m"
    BRONZE_BG = "\x1b[48;2;204;120;81m"
    SILVER = "\x1b[38;2;177;180;183m"
    SILVER_BG = "\x1b[48;2;196;198;200m"
    GOLD = "\x1b[38;2;215;164;60m"
    GOLD_BG = "\x1b[48;2;215;164;60m"
    PLATINUM = "\x1b[38;2;152;216;186m"
    PLATINUM_BG = "\x1b[48;2;152;216;186m"
    EMERALD = "\x1b[38;2;0;216;133m"
    EMERALD_BG = "\x1b[48;2;0;216;133m"
    DIAMOND = "\x1b[38;2;95;159;240m"
    DIAMOND_BG = "\x1b[48;2;95;159;240m"
    MASTER = "\x1b[38;2;138;232;95m"
    MASTER_BG = "\x1b[48;2;138;232;95m"
    GRANDMASTER = "\x1b[38;2;139;111;255m"
    GRANDMASTER_BG = "\x1b[48;2;139;111;255m"
    CHAMPION = "\x1b[38;2;203;123;255m"
    CHAMPION_BG = "\x1b[48;2;203;123;255m"

    WHITE = '\x1b[38;2;255;255;255m'
    BLACK = '\x1b[38;2;0;0;0m'
    BOLD = '\033[1m'
    ITALIC = '\x1B[3m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
