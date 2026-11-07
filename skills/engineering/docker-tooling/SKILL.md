---
name: docker-tooling
description: "Prefer Docker over installing on the host, to keep the host clean. Use when about to install a package or tool (pip, npm, apt), or set up a project's tooling."
---

# Docker tooling

Run project tooling in Docker where possible to keep the host clean.

- Before installing a package or tool on the host (pip, npm, apt), check whether it can run in Docker instead: the project's image, or a one-off `docker run` of a published image.
- If the project already builds and runs on the host, keep using its setup. Don't containerize a working workflow.
- If Docker isn't practical, ask the user before installing anything on the host. Say what you'd install and why Docker won't work.
