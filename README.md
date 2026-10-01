# WattleFlow Core
![WattleFlow Logo](https://raw.githubusercontent.com/wattleflow/core/default/src/wattleflow/logo/wattleflow.png)
[![PyPI version](https://img.shields.io/pypi/v/wattleflow.svg)](https://pypi.org/project/wattleflow/)
[![Python versions](https://img.shields.io/pypi/pyversions/wattleflow.svg)](https://pypi.org/project/wattleflow/)
[![License](https://img.shields.io/pypi/l/wattleflow.svg)](https://github.com/wattleflow/core/blob/default/LICENSE)

---

*WattleFlow — graceful flow,*
*modular, scaled with purpose,*
*patterns guide the stream,*
*extensible, clear design,*
*built to last and grow.*

---

| Characteristic | Value |
| --- | --- |
| **Version** | [![PyPI version](https://img.shields.io/pypi/v/wattleflow.svg)](https://pypi.org/project/wattleflow/) |
| **License**              | [![License](https://img.shields.io/pypi/l/wattleflow.svg)](https://github.com/wattleflow/core/blob/default/LICENSE) |
| **Python Compatibility** | [![Python versions](https://img.shields.io/pypi/pyversions/wattleflow.svg)](https://pypi.org/project/wattleflow/)|
| **Maturity** | Beta |
| **Dependencies** | none — standard library only |
| **Documentation** | [wattleflow/documentation](https://github.com/wattleflow/documentation) |

# What it is

`wattleflow` is the core of the WattleFlow framework: the abstract interfaces every other
WattleFlow distribution implements, derived from the Gang of Four design patterns. It carries no
implementation and no third-party dependency, so its import closure is the standard library.

| Module | Interfaces |
| --- | --- |
| `creational` | factories, builders, prototypes |
| `structural` | adapters, facades, proxies, composites |
| `behavioural` | strategies, observers, iterators, commands |
| `concurrent` | concurrency contracts |
| `transactional` | units of work |
| `framework` | the domain primitives: workflow, pipeline, processor, driver, repository, blackboard, strategy, connection, document |

The interfaces are authoritative: they change only through a recorded decision (`DR-COR`
series in the documentation repository).

# Installation

```bash
pip install wattleflow
```

# Implementations

- [wattleflow-workflow](https://github.com/wattleflow/workflow) — generic implementations and
  the data-engineering framework, standard library only.
- [blackwattle](https://github.com/wattleflow/blackwattle) — specialisations over third-party
  subsystems; not a zero-trust package.

# Licence

Apache-2.0 — see [LICENSE](LICENSE).
