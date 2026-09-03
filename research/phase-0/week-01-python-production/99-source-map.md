# 99 — Week 1 master source map

> Consolidated index of PEPs, docs, blogs, talks. Legal sources only.

---

## PEPs

| PEP | Topic | URL |
|-----|-------|-----|
| 484 | Type Hints | https://peps.python.org/pep-0484/ |
| 483 | Theory of type hints | https://peps.python.org/pep-0483/ |
| 420 | Implicit namespace packages | https://peps.python.org/pep-0420/ |
| 518 | pyproject.toml build-system | https://peps.python.org/pep-0518/ |
| 621 | Project metadata | https://peps.python.org/pep-0621/ |
| 612 | ParamSpec | https://peps.python.org/pep-0612/ |
| 695 | Type parameter syntax | https://peps.python.org/pep-0695/ |
| 735 | Dependency groups | https://peps.python.org/pep-0735/ |

---

## Official documentation

- typing: https://docs.python.org/3/library/typing.html  
- mypy existing code: https://mypy.readthedocs.io/en/stable/existing_code.html  
- mypy config: https://mypy.readthedocs.io/en/stable/config_file.html  
- mypyc: https://mypyc.readthedocs.io/en/latest/introduction.html  
- venv: https://docs.python.org/3/library/venv.html  
- logging HOWTO: https://docs.python.org/3/howto/logging.html  
- logging handlers: https://docs.python.org/3/library/logging.handlers.html  
- PyPA src vs flat: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/  
- setuptools discovery: https://setuptools.pypa.io/en/latest/userguide/package_discovery.html  
- setuptools editable: https://setuptools.pypa.io/en/latest/userguide/development_mode.html  
- pytest good practices: https://docs.pytest.org/en/latest/goodpractices.html  
- uv: https://docs.astral.sh/uv/  
- uv workspaces: https://docs.astral.sh/uv/concepts/projects/workspaces/  
- Poetry: https://python-poetry.org/docs/  
- Ruff: https://docs.astral.sh/ruff/  
- structlog: https://www.structlog.org/  
- Jupyter: https://jupyter.org/documentation  

---

## Industry blogs / case studies

- Dropbox mypy 4M lines: https://dropbox.tech/application/our-journey-to-type-checking-4-million-lines-of-python  
- Spring mypy: https://notes.crmarsh.com/using-mypy-in-production-at-spring  
- Hynek testing & packaging: https://hynek.me/articles/testing-packaging/  
- Ganssle test as installed: https://blog.ganssle.io/articles/2019/08/test-as-installed.html  
- uv vs Poetry: https://pydevtools.com/handbook/explanation/how-do-uv-and-poetry-compare/  
- PEP 735 explainer: https://pydevtools.com/handbook/explanation/what-is-pep-735/  
- src vs flat: https://pydevtools.com/handbook/explanation/src-layout-vs-flat-layout/  
- marimo intro: https://marimo.io/blog/introducing-marimo  
- marimo Python-not-JSON: https://marimo.io/blog/python-not-json  
- OTel Python logging: https://www.dash0.com/guides/opentelemetry-logging-python  

---

## YouTube / conference video

| Talk | Link |
|------|------|
| Joel Grus — I Don’t Like Notebooks (JupyterCon) | https://www.youtube.com/watch?v=7jiPeIFXb6U |
| MCoding — Modern Python logging | https://www.youtube.com/watch?v=9L77QExPmI0 |
| Dropbox / PyBay — mypy 4M lines (PyVideo) | https://pyvideo.org/pybay-2019/mypy-getting-to-four-million-lines-of-typed-python.html |
| Search hub: mypy Dropbox | https://www.youtube.com/results?search_query=mypy+four+million+lines+dropbox |

---

## GitHub

- python/mypy: https://github.com/python/mypy  
- astral-sh/uv: https://github.com/astral-sh/uv  
- uv BENCHMARKS: https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md  

---

## Syllabus build reminder

Refactor RAG chatbot → package (`src/`) + pytest skeleton + CI lint + type-check on every push. This corpus exists to make every choice in that refactor **explainable with citations**.
