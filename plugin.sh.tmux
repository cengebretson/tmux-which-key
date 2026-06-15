#!/usr/bin/env sh

set -e

#
# plugin.sh.tmux: initializes the plugin when tmux is started.
#
# TPM loads the plugin by executing all *.tmux files in the root directory, so
# this file has the "tmux" extension despite being a shell script.
#

# Resolve $0 to an absolute path, following symlinks. BSD/macOS readlink only
# gained `-f` in recent releases, so resolve links manually for portability.
resolve_path() {
    target="$1"
    while [ -L "$target" ]; do
        link="$(readlink "$target")"
        case "$link" in
            /*) target="$link" ;;
            *) target="$(dirname "$target")/$link" ;;
        esac
    done
    printf '%s\n' "$target"
}

root_dir="$(cd "$(dirname "$(resolve_path "$0")")" && pwd)"
config_file="$root_dir/config.yaml"
plugin_dir="$root_dir/plugin"
init_file="$plugin_dir/init.tmux"

# XDG

# create an XDG path and set the spec's default permissions of 0700 to newly
# created directories only
make_xdg_path() {
    OLDIFS=$IFS
    IFS='/'
    current_dir=""
    # walk the path to create each directory if it doesn't exist
    for dir in $1; do
        current_dir="$current_dir/$dir"
        # only create the directory and apply the mode it doesn't exist
        if [ ! -d "$current_dir" ]; then
            # shellcheck disable=SC2174
            # applying the mode to the deepest directory is intentional
            mkdir -m 0700 -p "$current_dir"
        fi
    done
    IFS=$OLDIFS
}

home_relative_path() {
    if ! command -v python3 >/dev/null; then
        echo "[tmux-which-key] python3 not found; XDG path resolution requires python3" >&2
        return 1
    fi

    python3 -c '
import sys
from pathlib import Path

home = Path(sys.argv[1]).expanduser().resolve(strict=False)
base = Path(sys.argv[2]).expanduser()
plugin_path = Path(sys.argv[3])

if plugin_path.is_absolute():
    raise SystemExit("[tmux-which-key] XDG plugin path must be relative")

target = (base / plugin_path).resolve(strict=False)
try:
    target.relative_to(home)
except ValueError:
    raise SystemExit("[tmux-which-key] XDG plugin path is outside of HOME: {}".format(target))

print(target)
' "$HOME" "$1" "$2"
}

case "$(tmux show-option -gvq @tmux-which-key-xdg-enable)" in
    1 | true)
        if [ -z "$HOME" ]; then
            echo "[tmux-which-key] HOME is not set.  XDG support is limited to users only."
            exit 1
        fi

        # use XDG spec's default directories if not set
        XDG_CONFIG_HOME=${XDG_CONFIG_HOME:-$HOME/.config}
        XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

        # get relative XDG path for the plugin or use the default
        xdg_plugin_path=$(tmux show-option -gvq @tmux-which-key-xdg-plugin-path)
        xdg_plugin_path=${xdg_plugin_path:-tmux/plugins/tmux-which-key}

        # Create XDG paths if they don't exist, and ensure they stay inside
        # $HOME.  macOS realpath does not support GNU --relative-to.
        xdg_config_path="$(home_relative_path "$XDG_CONFIG_HOME" "$xdg_plugin_path")"
        xdg_data_path="$(home_relative_path "$XDG_DATA_HOME" "$xdg_plugin_path")"
        make_xdg_path "$xdg_config_path"
        make_xdg_path "$xdg_data_path"

        # use the XDG paths
        config_file="$xdg_config_path/config.yaml"
        init_file="$xdg_data_path/init.tmux"
        ;;
esac

# /XDG

# Copy the default configs to the root directory if they don't exist yet. The
# root files are gitignored so users can customize them without breaking git
# updates.
if [ ! -f "$config_file" ]; then
    cp "$root_dir/config.example.yaml" "$config_file"
fi
if [ ! -f "$init_file" ]; then
    cp "$plugin_dir/init.example.tmux" "$init_file"
fi

# If enabled, rebuild the menu from the user config.
case "$(tmux show-option -gvq @tmux-which-key-disable-autobuild)" in
    1 | true) ;;
    *)
        # shellcheck disable=SC3013  # -nt is supported by the shells tmux runs (dash/bash/busybox)
        if [ "$config_file" -nt "$init_file" ]; then
            echo "[tmux-which-key] Rebuilding menu ..."
            if command -v python3 >/dev/null; then
                "$plugin_dir/build.py" "$config_file" "$init_file"
            else
                echo "[tmux-which-key] python3 not found"
            fi
        fi
        ;;
esac

# Load the plugin.
tmux source-file "$init_file"
