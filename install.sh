#!/usr/bin/env bash
set -euo pipefail

# Resolve this script's own directory -- i.e. wherever this repo actually
# lives on THIS machine -- regardless of where it was cloned to or what
# directory you're running this script from.
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/owtracker" << WRAPPER
#!/usr/bin/env bash
cd "$REPO_DIR" && uv run main.py
WRAPPER

chmod +x "$BIN_DIR/owtracker"

echo "Installed 'owtracker' -> $BIN_DIR/owtracker (pointing at $REPO_DIR)"

case ":$PATH:" in
    *":$BIN_DIR:"*)
        echo "You're all set -- try running: owtracker"
        ;;
    *)
        echo ""
        echo "NOTE: $BIN_DIR isn't on your PATH yet. Add it, then restart your terminal:"
        echo "  bash/zsh (~/.bashrc or ~/.zshrc):   export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo "  fish (~/.config/fish/config.fish):  fish_add_path \$HOME/.local/bin"
        ;;
esac
