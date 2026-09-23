#!/bin/bash
# ~/.bashrc: executed by bash(1) for non-login shells.

# Exit if not running interactively.
case $- in
    *i*) ;;
      *) return 0 ;;
esac

#######################################################
# 1. STARTUP
#######################################################

function __install_cowsay_if_missing {
    if command -v cowsay >/dev/null 2>&1; then
        return 0
    fi

    if command -v apt-get >/dev/null 2>&1; then
        if [ "$(id -u)" -eq 0 ]; then
            apt-get update -y >/dev/null 2>&1 && apt-get install -y cowsay >/dev/null 2>&1
            return 0
        fi
        if command -v sudo >/dev/null 2>&1; then
            sudo apt-get update -y >/dev/null 2>&1 && sudo apt-get install -y cowsay >/dev/null 2>&1
            return 0
        fi
    fi

    if command -v dnf >/dev/null 2>&1; then
        if [ "$(id -u)" -eq 0 ]; then
            dnf install -y cowsay >/dev/null 2>&1
            return 0
        fi
        if command -v sudo >/dev/null 2>&1; then
            sudo dnf install -y cowsay >/dev/null 2>&1
            return 0
        fi
    fi

    if command -v pacman >/dev/null 2>&1; then
        if [ "$(id -u)" -eq 0 ]; then
            pacman -Sy --noconfirm cowsay >/dev/null 2>&1
            return 0
        fi
        if command -v sudo >/dev/null 2>&1; then
            sudo pacman -Sy --noconfirm cowsay >/dev/null 2>&1
            return 0
        fi
    fi
}

function __random_cow_palette {
    case $((RANDOM % 8)) in
        0) printf '%s\n' '1;33' '0;31' '0;35' ;;
        1) printf '%s\n' '1;31' '0;35' '0;34' ;;
        2) printf '%s\n' '1;34' '0;36' '0;35' ;;
        3) printf '%s\n' '1;36' '0;34' '0;33' ;;
        4) printf '%s\n' '1;33' '0;35' '0;36' '0;34' ;;
        5) printf '%s\n' '1;31' '0;33' '0;35' '0;34' ;;
        6) printf '%s\n' '1;35' '0;34' '0;36' '0;33' ;;
        *) printf '%s\n' '1;33' '0;31' '0;34' '0;36' ;;
    esac
}

function colorize_cow {
    local bubble_offset=$((RANDOM % 4))
    local palette_csv
    local start_offset=$((RANDOM % 4))
    local -a palette

    if [ ! -t 1 ] || [ -n "${NO_COLOR:-}" ] || [ "${TERM:-}" = "dumb" ]; then
        cat
        return 0
    fi

    mapfile -t palette < <(__random_cow_palette)
    if [ "${#palette[@]}" -eq 0 ]; then
        cat
        return 0
    fi

    palette_csv=$(IFS=,; printf '%s' "${palette[*]}")

    awk -v palette="$palette_csv" -v start_offset="$start_offset" -v bubble_offset="$bubble_offset" '
        BEGIN {
            reset = sprintf("%c[0m", 27)
            count = split(palette, colors, ",")
            line_index = 0
            bubble_done = 0
            bubble_line_count = 0
        }
        {
            if ($0 ~ /^[[:space:]]*$/) {
                print $0
                next
            }

            if (!bubble_done) {
                color = colors[((bubble_line_count + bubble_offset) % count) + 1]
                bubble_line_count++
                if ($0 ~ /^[[:space:]]*[-_][-_ -]*[[:space:]]*$/) {
                    if (bubble_line_count > 1) {
                        bubble_done = 1
                        line_index = 0
                    }
                }
            } else {
                color = colors[((line_index + start_offset) % count) + 1]
                line_index++
            }

            printf "%c[%sm%s%s\n", 27, color, $0, reset
        }
    '
}

function __random_cow_message {
    printf '%s\n' \
        "Shell ready." "Systems online." "Charting course." "Winds favorable." \
        "Another terminal, another mission." "All hands on deck." "We are so back." \
        "It works on my shell." "Task failed successfully." "Zero bugs, only features." \
        "Vibes: deployed." "Ship it and blame cache." "Entering goblin mode." \
        "Certified terminal moment." "No thoughts, just commands." "Born to grep." \
        "Today's forecast: mostly aliases." "No context, only confidence." \
        "All gas, no stack trace." "The shell is shelling." "Live laugh launch." \
        "Another day, another yak." "Main character in a tmux pane." \
        "Rawdogging production with optimism." "Grepping for meaning." \
        "Locally sourced command line nonsense." "PRs fear this terminal." \
        "Keyboard hot, tea hotter." "Trust the process. Verify the output." \
        "We ball until the tests fail." "Everything is fine. Fire is just light." \
        "Works on my machine. ¯\_(ツ)_/¯" "One sudo to rule them all." \
        "The cloud is just someone else's computer on fire." "I think, therefore I grep." \
        "To err is human, to ssh is divine." "Lost in the sauce, found in the logs." \
        "Delusional but making progress." "Big Shell Energy." "POV: You forgot the semicolon." \
        "Manifesting a successful build." "Stay humble, stay chmod." \
        "Slaying the monolith, one script at a time." "Exit code 0. We're chilling." \
        "Pipe it to /dev/null and forget your sins." "My spirit animal is a zombie process." \
        "Vim: I'm still trying to leave." "Gaslight, Gatekeep, Grep." \
        "I'm not a robot, but my cron jobs are." "It's not a bug, it's a surprise mechanic." \
        "Code is poetry. Mine is a limerick." "99 little bugs in the code..." \
        "LGTM (I didn't actually look at it)." "Technical debt is a gift for my future self." \
        "Writing documentation is admitting defeat." "Running on caffeine and control + r." \
        "Is it local time or is it just me?" "Scanning for intelligent life... 0 results." \
        "My other computer is your computer." "I'm in. (On the third try)." \
        "Don't touch that. It's a load-bearing comment." "Packet loss is my love language." \
        "Delete node_modules. Start your life over." "Stress level: rm -rf /" \
        "If you can't handle my fork bomb, you don't deserve my uptime." \
        "Go girl, give us nothing (but exit code 0)." "I use Vim because I am trapped." \
        "The abyss stares back, but I have syntax highlighting." \
        "The horrors persist, but so do I." "Chat, are we cooked?" \
        "Many such cases." "This meeting could have been a grep." \
        "I am once again asking for a reproducible bug." \
        "Nothing ever happens. Until prod." "We stay silly in this house." \
        "Sending thoughts and packets." "Mood: dangerously overfit to localhost." \
        "Hate from outside the repo can't even reach me." \
        "Built different. Broken the same." "The pipeline yearns for violence." \
        "What if the real stack trace was the friends we made along the way." \
        "In my defense, the logs were vibes-based." \
        "This shell has seen things." "All my homies love idempotence." \
        "I did it for the bit and now the bit is in production." \
        "Skill issue. Terminal issue. User issue. Cosmic issue." \
        "Runtime is temporary. Screenshots are forever." \
        "You're telling me a script fried this rice?" \
        "Screaming, crying, throwing semicolons." \
        "We got observability at home." "The bug was inside us all along." \
        "Too locked in to log off." "I support women's wrongs and broken builds." \
        "This environment is cursed but stable." \
        "Respectfully, what is going on." "Terminally online, literally." \
        "I have the opportunity to do the funniest thing." \
        "This commit has bad energy." "Who up tracing they root cause." \
        "I bring a sort of shell energy that production fears." \
        "I am not built for this timezone." \
        "The code compiles and that is between it and God." \
        "All natural, locally sourced artisanal technical debt." \
        "First try? We don't do that here." "No weapon formed against me shall prosper, except YAML." \
        "Cowabunga it is." "You ever just inherit a codebase and blink a lot?" \
        "This is my emotional support terminal." \
        "I know what you are: a race condition." \
        "On my worst behavior and best branch." | shuf -n 1
}

function __random_startup_cow {
    local cows_dir="$HOME/.cows/cowsay-files/cows"
    local custom_cows_dir="$HOME/.cows/custom-cows"
    local message
    local random_cow
    local rendered

    if ! command -v cowsay >/dev/null 2>&1; then
        return 0
    fi

    message="$(__random_cow_message)"
    random_cow=$(find "$cows_dir" "$custom_cows_dir" -type f -name '*.cow' -not -path '*/.git/*' -print0 2>/dev/null | xargs -0 -r grep -L '\\e\[' | shuf -n 1)

    if [ -z "$random_cow" ]; then
        return 0
    fi

    rendered=$(cowsay -W 40 -f "$random_cow" "$message" 2>/dev/null)
    if [ -n "$rendered" ]; then
        printf '%s\n' "$rendered" | colorize_cow
    fi
}

function setup_cows {
    local no_install="${1:-}"
    local cows_dir="$HOME/.cows"
    local cows_repo="https://github.com/paulkaefer/cowsay-files"
    local repo_dir="$cows_dir/cowsay-files"

    mkdir -p "$cows_dir"

    if command -v git >/dev/null 2>&1; then
        if [ ! -d "$repo_dir/.git" ]; then
            git clone --depth=1 "$cows_repo" "$repo_dir" >/dev/null 2>&1
        else
            git -C "$repo_dir" pull --ff-only >/dev/null 2>&1
        fi
    fi

    if [ "$no_install" != "--no-install" ]; then
        __install_cowsay_if_missing
    fi

    __random_startup_cow
}

__random_startup_cow

#######################################################
# 2. SHELL OPTIONS & HISTORY
#######################################################

export HISTCONTROL=ignoreboth
export HISTSIZE=10000
export HISTFILESIZE=20000
shopt -s histappend
shopt -s checkwinsize

#######################################################
# 3. ENVIRONMENT
#######################################################

export EDITOR=vi
export VISUAL=vi
export REPO_DIR="$HOME/Repos"

#######################################################
# 4. PROMPT
#######################################################

function __setprompt {
    local RESET="\[\e[0m\]"
    local CYAN="\[\e[36m\]"
    local BLUE="\[\e[34m\]"
    local GREEN="\[\e[32m\]"
    local MAGENTA="\[\e[35m\]"
    local git_branch

    PS1="${CYAN}\u${RESET}${BLUE}:\w${RESET}"

    if type __git_ps1 >/dev/null 2>&1; then
        # Some git prompt scripts expand unset GIT_PS1_* vars; run with nounset disabled.
        git_branch="$( (set +u; __git_ps1 '(%s)') )"
        if [ -n "$git_branch" ]; then
            PS1+=" ${MAGENTA}${git_branch}${RESET}"
        fi
    fi

    if [ -n "${VIRTUAL_ENV:-}" ]; then
        PS1+=" ${GREEN}($(basename "$VIRTUAL_ENV"))${RESET}"
    fi

    PS1+=" \$ "
}

PROMPT_COMMAND='history -a; history -n; __setprompt'

#######################################################
# 5. ALIASES & FUNCTIONS
#######################################################

if [ -x /usr/bin/dircolors ]; then
    test -r "$HOME/.dircolors" && eval "$(dircolors -b "$HOME/.dircolors")" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias c='clear'
alias alert='notify-send --urgency=low -i "$( (($? == 0)) && echo terminal || echo error )" "$(history | tail -n1 | sed -e '\''s/^\s*[0-9]\+\s*//; s/[;&|]\s*alert$//'\'')"'

if command -v vim >/dev/null 2>&1; then
    alias vi='vim'
fi

function dcd {
    local name="$1"
    local match

    if [ -z "$name" ]; then
        echo "Usage: dcd <folder-name>"
        return 1
    fi

    match=$(find . -maxdepth 6 -type d -name "$name" -print -quit 2>/dev/null)

    if [ -z "$match" ]; then
        echo "No folder named '$name' found within 6 levels from $(pwd)."
        return 1
    fi

    cd "$match" || return 1
}

function ucd {
    local name="$1"
    local dir="$PWD"

    if [ -z "$name" ]; then
        echo "Usage: ucd <folder-name>"
        return 1
    fi

    while [ "$dir" != "/" ]; do
        if [ "$(basename "$dir")" = "$name" ]; then
            cd "$dir" || return 1
            return 0
        fi
        dir="$(dirname "$dir")"
    done

    if [ "$name" = "/" ]; then
        cd / || return 1
        return 0
    fi

    echo "No parent folder named '$name' found above $(pwd)."
    return 1
}

gdiffcode() {
    # Check if inside a git repository
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "Error: Not inside a git repository." >&2
        return 1
    fi

    # Use a fixed temporary file with a .diff extension
    local diff_file="${TMPDIR:-/tmp}/git_changes.diff"

    {
        # 1. Diff for all tracked changes
        git diff HEAD

        # 2. Diff for untracked files
        git ls-files --others --exclude-standard | while IFS= read -r file; do
            git diff --no-index /dev/null "$file"
        done
    } > "$diff_file"

    # Only open VS Code if there are actual changes
    if [ -s "$diff_file" ]; then
        code "$diff_file"
    else
        echo "No uncommitted changes found."
    fi
}

gdiffwatch() {
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "Error: Not inside a git repository." >&2
        return 1
    fi

    local diff_file="${TMPDIR:-/tmp}/git_changes.diff"
    local new_diff="${TMPDIR:-/tmp}/git_changes_new.tmp"

    trap 'rm -f "$new_diff"; return 0' INT TERM

    touch "$diff_file"
    code "$diff_file"

    while true; do
        {
            git diff HEAD
            git ls-files --others --exclude-standard | while IFS= read -r file; do
                git diff --no-index /dev/null "$file" 2>/dev/null
            done
        } > "$new_diff"

        if ! cmp -s "$new_diff" "$diff_file"; then
            cp "$new_diff" "$diff_file"
        fi

        sleep 10
    done
}

#######################################################
# 6. COMPLETIONS & SOURCING
#######################################################

if [ -f /etc/bashrc ]; then . /etc/bashrc; fi

if [ -r "/usr/share/bash-completion/bash_completion" ]; then
    . "/usr/share/bash-completion/bash_completion"
elif [ -r "/etc/bash_completion" ]; then
    . "/etc/bash_completion"
fi

if [ -f /usr/share/git-core/contrib/completion/git-prompt.sh ]; then
    . /usr/share/git-core/contrib/completion/git-prompt.sh
fi

if [ -f "$HOME/.bash_aliases" ]; then . "$HOME/.bash_aliases"; fi

if [ -x /usr/bin/lesspipe ]; then eval "$(lesspipe)"; fi

#######################################################
# 7. LOCAL WORK CONFIG
#######################################################

if [ -f "$HOME/.workrc" ]; then . "$HOME/.workrc"; fi
. "$HOME/.cargo/env"

# opencode
export PATH="$HOME/.opencode/bin:$PATH"
