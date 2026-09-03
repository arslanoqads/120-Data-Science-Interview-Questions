# 02 — Project structure (src layout vs flat)

> Week 1 concept research (deep). Legal sources only.

---

## Fundamentals

### Two layouts
**Flat layout:** importable package directory sits beside `pyproject.toml`, `tests/`, README at repo root (`mypkg/` next to config).  
**Src layout:** importable code lives under `src/mypkg/` (or `src/deployment_copilot/`). Tests and config stay at root.

### Why Python makes this matter
The interpreter puts **cwd on `sys.path` first**. In a flat layout, `import mypkg` during `pytest` often imports the **local source tree**, not the **installed** distribution. Packaging mistakes (missing package data, forgotten subpackage, empty wheel) go unnoticed until Docker/`pip install` in CI or prod.

**Src layout** keeps the package off the default path unless installed (editable or regular). Tests then fail loudly with `ModuleNotFoundError` until `uv sync` / `pip install -e .` — which is the desired signal.

PyPA: src layout “helps prevent accidental usage of the in-development copy of the code” and avoids editable installs accidentally importing README/tox config as modules.

### Editable installs
`pip install -e .` / uv editable sync installs metadata + path hooks so edits reflect immediately. Setuptools “strict” editable mode (`editable_mode=strict`) mimics regular installs more closely (file link farm) when default editable behavior is too loose.

---

## Alternatives & Tradeoffs

| Layout / pattern | Pros | Cons |
|------------------|------|------|
| Flat | REPL-friendly; less ceremony; common in apps | Tests can false-green; import path pollution; accidental multi-package discovery |
| Src | Install-faithful tests; cleaner discovery; Hynek/pytest recommended | Needs editable install; slightly worse “just run python” |
| `uv init --no-package` flat scripts | Fine for one-off tools | Wrong for shippable FastAPI services |
| Monorepo `packages/<name>/` (with or without `src/`) | Clear multi-service boundaries | Need workspace tooling (uv workspaces) |
| In-package tests (`mypkg/tests`) | Colocation | Risk of shipping tests; import confusion |

Hynek Schlawack (“Testing & Packaging”): historically scoffed at src; converted after tox tests ran against the wrong code and after seeing cryptography adopt src. 2021 update: Flask, Pyramid, Twisted moved to src; “NASA … use src directories.” Motto: die on the *correct* hill vs easy.

pytest good practices: especially with default import mode `prepend`, **strongly suggest src layout**.

### setuptools discovery config (src)
```toml
[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```
Hatch/Flit/Poetry/uv often detect src automatically.

---

## Necessity

### Failure modes
1. **Empty or incomplete wheels** — tests passed against cwd; prod missing templates/chunkers.  
2. **`PYTHONPATH=.` in Docker** papers over broken packaging; diverges from local uv env.  
3. **Name collisions** — a script `openai.py` or `test_utils.py` shadows libraries.  
4. **Interview signal failure** — reviewers open repo, see notebook debris at root, no package.  
5. **Coverage lies** — Hynek: coverage measured against source tree while tox installed a different artifact; need Coverage.py `[paths]` mapping `src` ↔ site-packages.

### RAG chatbot specifics
Resource files (prompt templates, chunking configs, JSON schemas) must be declared as package data. Src layout + install-faithful tests catch “forgot to include `prompts/*.md` in the wheel” before Cloud Run.

---

## Industry Practice

### Common
```
repo/
  app.py
  utils.py
  requirements.txt
  test_app.py
```
Or flat `app/` with `PYTHONPATH` hacks.

### Senior
```
repo/
  pyproject.toml
  uv.lock
  .python-version
  src/
    deployment_copilot/
      __init__.py
      api/
      domain/
      adapters/
      py.typed          # if shipping types
  tests/
  prompts/             # or under package resources
  Dockerfile
```
- Editable install in CI before pytest.  
- Console scripts via `[project.scripts]`.  
- No reliance on cwd imports.  
- `uv init` defaults toward src for packages.

### Application-only services
Even if never published to PyPI, src layout still pays off for **image builds** (`uv sync --frozen` + install package) and install-faithful tests. Flat can be OK for true internal scripts—not for the flagship system.

---

## Concrete Scenario

Hynek’s bug: tox/Coverage setup “worked by accident”—tests did not run against the installed app. Fix: move to src so the only way to import is via install. Combined coverage across tox envs then needs Coverage `[paths]` to map `src` and `.tox/.../site-packages`.

Primary docs:
- https://hynek.me/articles/testing-packaging/  
- https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/  
- https://docs.pytest.org/en/latest/goodpractices.html  
- https://setuptools.pypa.io/en/latest/userguide/package_discovery.html  
- https://setuptools.pypa.io/en/latest/userguide/development_mode.html  

Paul Ganssle “Test as installed”: https://blog.ganssle.io/articles/2019/08/test-as-installed.html

---

## Open Questions

1. For Cloud Run-only apps, is `src/` still worth it vs a single `app` package with explicit tox `changedir`? (Research lean: yes, for interview + packaging discipline.)  
2. Should prompt templates live in-package (`importlib.resources`) or as mounted ConfigMaps? (Affects layout and Week 5.)  
3. Namespace packages (PEP 420) + flat layout still experimental in setuptools—prefer src if using namespaces.  
4. How to teach src layout without blocking REPL exploration for TPM→engineer transitions? (`uv run python`)

---

## Sources

- https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/  
- https://hynek.me/articles/testing-packaging/  
- https://docs.pytest.org/en/latest/goodpractices.html  
- https://setuptools.pypa.io/en/latest/userguide/package_discovery.html  
- https://setuptools.pypa.io/en/latest/userguide/development_mode.html  
- https://blog.ganssle.io/articles/2019/08/test-as-installed.html  
- https://pydevtools.com/handbook/explanation/src-layout-vs-flat-layout/  
- https://peps.python.org/pep-0420/  
