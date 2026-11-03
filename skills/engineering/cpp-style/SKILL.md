---
name: cpp-style
description: "My C++ style: naming, constants, string_view, optional, const, and header docs. Use when writing, editing, or reviewing C++."
---

# C++ style

The repo's own style guide wins where it disagrees. Write comments and docs in the `deslop` style.

- Use descriptive identifiers, except obvious local indices and coordinates.
- Prefix enum values and namespace-scope constants with `k` (`kFollowing`, `kMaxTrackIndex`).
- Replace protocol, hardware, and sensor magic numbers with named constants in a domain header, each with a short comment giving its bound or wire meaning.
- Reuse existing conversion utilities instead of repeating the arithmetic.
- Use `std::string_view` for non-owning constant strings and returns.
- In compound `std::optional` conditions, write `has_value()` and `value()` explicitly.
- Mark computed values `const` when nothing changes them later.
- Document every function declaration in headers, private helpers included. Group overrides under one comment only when that comment defines each one's contract.
