#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="$HOME"
COPY_MODE=false
FORCE_YES=false

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --copy)
            COPY_MODE=true
            ;;
        -y|--yes)
            FORCE_YES=true
            ;;
        --help|-h)
            echo "Usage: $0 [--copy] [-y]"
            echo ""
            echo "Sets up dotfiles by symlinking config files from this repo into \$HOME."
            echo ""
            echo "Options:"
            echo "  --copy    Copy files instead of creating symlinks (resolves symlinked skill directories)"
            echo "  -y, --yes Skip all confirmation prompts (force overwrite)"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
done

# Colors
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

warn()    { echo -e "${YELLOW}WARNING:${NC} $*"; }
success() { echo -e "${GREEN}OK:${NC} $*"; }

# Prompt for confirmation before an overwrite or removal, honoring -y/--yes.
# $1 = verb shown in the prompt ("Overwrite"/"Remove"), $2 = target path,
# $3 = reason shown in the warning (e.g. "already exists").
# Returns 0 if should proceed, 1 if should skip.
confirm_action() {
    local verb="$1" target="$2" reason="$3"
    if [ "$FORCE_YES" = true ]; then
        return 0
    fi
    warn "'$target' $reason."
    read -r -p "$verb? [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) echo "Skipping '$target'."; return 1 ;;
    esac
}

# Remove an existing file, symlink, or directory at $1.
remove_existing() {
    local target="$1"
    if [ -L "$target" ]; then
        rm "$target"
    elif [ -d "$target" ]; then
        rm -rf "$target"
    elif [ -f "$target" ]; then
        rm "$target"
    fi
}

# If dest exists, confirm overwrite and remove it. Returns 1 if the caller should skip.
clear_for_overwrite() {
    local dest="$1"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        confirm_action "Overwrite" "$dest" "already exists" || return 1
        remove_existing "$dest"
    fi
}

# Link or copy a single file/directory.
# $1 = source (absolute path inside repo)
# $2 = destination (absolute path in $HOME)
install_item() {
    local src="$1"
    local dest="$2"

    if [ "$COPY_MODE" = false ]; then
        # If dest is already a symlink pointing to the right place, nothing to do.
        if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
            success "Already linked '$dest'"
            return 0
        fi
    fi

    mkdir -p "$(dirname "$dest")"
    clear_for_overwrite "$dest" || return 0

    if [ "$COPY_MODE" = true ]; then
        # -L: follow symlinks so symlinked dirs (e.g. skill-creator) are copied as real dirs
        cp -rL "$src" "$dest"
        success "Copied '$src' -> '$dest'"
    else
        ln -s "$src" "$dest"
        success "Symlinked '$src' -> '$dest'"
    fi
}

# Install all items directly under a source directory into a destination directory.
install_dir_items() {
    local src_dir="$1"
    local dest_dir="$2"

    [ -d "$src_dir" ] || return 0

    for item in "$src_dir"/*; do
        [ -e "$item" ] || continue
        install_item "$item" "$dest_dir/$(basename "$item")"
    done
}

# Remove items in a destination directory that no longer have a corresponding
# item in the source directory (e.g. a skill removed/renamed upstream), so old
# installs don't linger and confuse things.
prune_removed_items() {
    local src_dir="$1"
    local dest_dir="$2"

    [ -d "$dest_dir" ] || return 0

    for existing in "$dest_dir"/*; do
        { [ -e "$existing" ] || [ -L "$existing" ]; } || continue
        local name
        name="$(basename "$existing")"
        if { [ -e "$src_dir/$name" ] || [ -L "$src_dir/$name" ]; }; then
            continue
        fi
        confirm_action "Remove" "$dest_dir/$name" "is stale (no longer present in source)" || continue
        remove_existing "$existing"
        success "Removed stale '$dest_dir/$name'"
    done
}

# Remove repo-internal symlinks under dest_rel_dir that point into
# target_rel_dir (i.e. were previously created by link_dir_in_repo) but whose
# source item no longer exists (e.g. a skill removed/renamed upstream).
# Only touches symlinks matching target_rel_dir, leaving first-party items alone.
prune_stale_repo_links() {
    local src_dir="$1"
    local dest_rel_dir="$2"
    local target_rel_dir="$3"

    local full_dest_dir="$REPO_DIR/$dest_rel_dir"
    [ -d "$full_dest_dir" ] || return 0

    for item in "$full_dest_dir"/*; do
        [ -L "$item" ] || continue
        local link_target
        link_target="$(readlink "$item")"
        case "$link_target" in
            "$target_rel_dir"/*) ;;
            *) continue ;;
        esac
        local name
        name="$(basename "$item")"
        if [ -e "$src_dir/$name" ]; then
            continue
        fi
        confirm_action "Remove" "$dest_rel_dir/$name" "is stale (no longer present in source)" || continue
        rm "$item"
        success "Removed stale repo-link '$dest_rel_dir/$name'"
    done
}

# --- Repo-internal symlinks ---
# Disabled for now.
# Creates relative symlinks inside the repo so browsing .agents/
# shows skills from submodules alongside first-party files.
# Always symlinks (never copies), regardless of --copy mode.
# echo ""
# echo "Updating repo-internal symlinks..."

link_in_repo() {
    local dest_rel="$1"   # path relative to repo root, e.g. .copilot/skills/brainstorming
    local link_target="$2" # relative target for the symlink itself, e.g. ../../.obra.superpowers/skills/brainstorming

    local full_dest="$REPO_DIR/$dest_rel"
    mkdir -p "$(dirname "$full_dest")"

    if [ -L "$full_dest" ] && [ "$(readlink "$full_dest")" = "$link_target" ]; then
        success "Already linked '$dest_rel'"
        return 0
    fi

    clear_for_overwrite "$full_dest" || return 0

    ln -s "$link_target" "$full_dest"
    success "Repo-linked '$dest_rel' -> '$link_target'"
}

# Link all items directly under a source directory into a repo-relative destination directory.
link_dir_in_repo() {
    local src_dir="$1"
    local dest_rel_dir="$2"
    local target_rel_dir="$3"

    [ -d "$src_dir" ] || return 0

    for item in "$src_dir"/*; do
        [ -e "$item" ] || continue
        local name
        name="$(basename "$item")"
        link_in_repo "$dest_rel_dir/$name" "$target_rel_dir/$name"
    done
}

echo ""
if [ "$COPY_MODE" = true ]; then
    echo "Mode: COPY"
else
    echo "Mode: SYMLINK"
fi
echo "Repo:   $REPO_DIR"
echo "Target: $HOME_DIR"
echo ""

# --- Items to install ---
# Format: source path (relative to repo) -> destination path (relative to $HOME)

install_item "$REPO_DIR/.bashrc"           "$HOME_DIR/.bashrc"
install_item "$REPO_DIR/.tmux.conf"        "$HOME_DIR/.tmux.conf"
install_item "$REPO_DIR/.vimrc"            "$HOME_DIR/.vimrc"
install_item "$REPO_DIR/.cows/custom-cows" "$HOME_DIR/.cows/custom-cows"


# Install first-party and local Copilot skills directly from this checkout.
# demo installs locked npm assets on first use.
prune_removed_items "$REPO_DIR/.copilot/skills" "$HOME_DIR/.copilot/skills"
install_dir_items "$REPO_DIR/.copilot/skills" "$HOME_DIR/.copilot/skills"

# .copilot instructions (global, applies across all workspaces)
prune_removed_items "$REPO_DIR/.copilot/instructions" "$HOME_DIR/.copilot/instructions"
install_dir_items "$REPO_DIR/.copilot/instructions" "$HOME_DIR/.copilot/instructions"

echo ""
echo "Done."
