---
name: project-setup
description: 'Configure a repository with an orchestrator workflow, Dockerized tooling, an LLM wiki ticket board, and Matt Pocock engineering skills.'
disable-model-invocation: true
---

# Project Setup

1. Act as an orchestrator managing sub-agents, keeping token consumption minimal throughout the project.
2. Use Docker to keep the host environment clean.
3. Seed `AGENTS.md` with the baseline rules from https://github.com/DietrichGebert/ponytail/blob/2a1fe842d078cf66ec7f3e6096a8ca4279c2cad7/AGENTS.md (raw: https://raw.githubusercontent.com/DietrichGebert/ponytail/2a1fe842d078cf66ec7f3e6096a8ca4279c2cad7/AGENTS.md). Copy only those general rules; do not install the `ponytail` skill.
4. Create the project wiki and ticket board with the `llm-wiki` skill.
5. Install https://github.com/mattpocock/skills into the project if not installed globally. Run its `setup-matt-pocock-skills` skill with the defaults and the wiki as the issue tracker, and use the skills whenever applicable.
6. Record these model defaults in AGENTS.md and follow them: use Haiku- or Luna-class models for simple tasks and Sonnet- or Sol-class models for implementation; use Opus- or Astra-class models for orchestration, architecture, design, and complex or stuck tasks.
