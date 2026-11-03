---
name: user-run-commands
description: "Hand the user a command block to run when the agent can't run it itself (hardware, another machine, a cluster, sudo, a VPN), then read the report back. Use whenever the user must run a command or diagnostic for you."
---

# User-run commands

When the user has to run something for you, give them one block they can paste and leave alone, and read its output yourself. Never ask them to paste output back.

## The block

One bounded, non-interactive block that writes stdout and stderr to `/tmp/<topic>-check.txt`:

- Put `REPORT` and every value the user might change at the top, and check them before use.
- Run the body in a subshell `( ... )` so `set`, `exit`, and `cd` can't touch the user's shell. Use `set -uo pipefail`, or `set -euo pipefail` when a failed step should stop the rest (build, push, deploy).
- Wrap network probes in `timeout`. For SSH use `ssh -n` or `</dev/null`, never a heredoc.
- Log `date -Is` and the resolved identifiers (host, branch, version) so the report stands alone.
- Add `|| true` to probes that are expected to fail, and print a greppable `key=true|false` line for each check.
- Print `printf '<Topic> report: %s\n' "$REPORT"` after the subshell, outside the redirect.

```bash
REPORT=/tmp/network-check.txt
HOST=example.local
(
  set -uo pipefail
  [[ -n "$HOST" ]] || { echo "HOST is empty"; exit 2; }
  date -Is
  echo "host=$HOST"
  timeout 5 ping -c1 "$HOST" >/dev/null && echo "reachable=true" || echo "reachable=false"
  timeout 5 ssh -n -o BatchMode=yes "$HOST" uptime && echo "ssh=true" || echo "ssh=false"
  journalctl -u myservice -n 20 --no-pager || true
) > "$REPORT" 2>&1
printf 'Network report: %s\n' "$REPORT"
```

End your turn with the literal line `<Topic> report: /tmp/<topic>-check.txt` so the path is unambiguous.

## Reading the report

1. When the user says it ran, read the report file yourself.
2. Keep what the report shows apart from what you infer from it.
3. Treat branch, `HEAD`, network, credentials, cluster context, running processes, and deployed artifacts as stale after anything that could change them; check again rather than reuse an old report.
4. Confirm a fix at the boundary that failed, against the running artifact and its config. A successful build, push, or deploy alone doesn't prove the fix.

For a multi-step walkthrough the user must click or type through, use the `wizard` skill instead.
