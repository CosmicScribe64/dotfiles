# Fixture sources

These files measure `scripts/find_tells.py` hit rates. They are test data, not
style examples.

## human/

- `pep-*.rst`: Python Enhancement Proposals 1, 8, 20, 257, 343, and 484, from
  [python/peps](https://github.com/python/peps), created 2000 to 2014. Each PEP
  states that it has been placed in the public domain.
- `textwrap.py`, `shlex.py`: CPython 3.8.0 standard library, from
  [python/cpython](https://github.com/python/cpython/tree/v3.8.0/Lib), released
  2019. Copyright Python Software Foundation, used under the
  [PSF License Agreement](https://docs.python.org/3/license.html).

## ai/

- `wikipedia-examples.md`: AI-generated passages quoted as examples on
  [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
  with the revision ids each example came from. Wikipedia text is available under
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); markup was
  stripped and the wording left unchanged.
- `agent_comments.py`, `agent_readme.md`: synthetic samples of coding-agent
  output written for this fixture set.
