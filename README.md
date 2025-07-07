# WattleFlow Core
![WattleFlow Logo](src/wattleflow/logo/wattleflow.png)

---
WattleFlow—graceful flow,
modular, scaled with purpose,
patterns guide the stream,
extensible, clear design,
built to last and grow.

---

# WattleFlow Core Framework
A modular framework for Python, that facilitate design patterns as an architectural building blocks to enable efficient architecure.

## Core Concepts:
- Design Patterns based on GoF (Gang of Four) Standards
- Modular Architecture
- Code Maintainability
- Scalability
- Minimal Dependencies within the Python Ecosystem

- **Design Patterns** - The solution follows proven software engineering principles based on the internationally recognised Gang of Four (GoF) design patterns. These patterns provide standardised, reusable solutions for common architectural and development challenges. Their adoption enhances code readability, promotes consistent system design, and ensures alignment with best practices in object-oriented development.

- **Modular Architecture** - The framework is following modular principles, where individual components (or interfaces) are developed, tested, and maintained independently. This enables flexibility, simplifies system evolution, and reduces the impact of changes on other parts of the solution design. Modular architecture also facilitates team collaboration by allowing parallel development across different functional units

- **Code Maintainability** - The system emphasises maintainable code, which reduces technical debt and simplifies ongoing development, testing, and debugging. Clean, well-structured, and documented code ensures long-term sustainability, making it easier for new team members to onboard and for existing teams to evolve the solution without introducing instability.

- **Scalablitlity** - Wattleflow is intended for scaling solutions both vertically and horizontally, ensuring that the system can efficiently handle increased workloads, higher data volumes, and a growing number of concurrent processes or users. Scalability is essential for maintaining system performance and reliability in high-demand environments, particularly in data-intensive or mission-critical operations.


- **Minimal Dependencies within the Python Ecosystem** - The solution is intentionally designed with minimal external dependencies, relying primarily on stable, well-supported components within the Python ecosystem. This reduces complexity, simplifies deployment, and minimises security risks associated with third-party packages. At the same time, it ensures compatibility with common data engineering tools and frameworks.

## Design Principles
Followign the guidelines from the book "Design Patterns: Elements of Reusable Object-Oriented Software" (commonly known as the "Gang of Four" or GoF), `Wattleflow` framework is based on the principles that have become the de facto standard in the software industry, particularly in:
- Object-Oriented Design (OOP)
- Development of Scalable Systems
- Enterprise Architecture
- Microservices and Distributed Systems

## Core Libraries
    - `__init__.py`
    - `behavioral.py`
    - `concurent.py`
    - `creational.py`
    - `framework.py`
    - `structural.py`
    - `transactional.py`

# Characteristics

| Characteristic           | Value                                                                   |
| ------------------------ | ----------------------------------------------------------------------- |
| **Version**              | v0.0.0.17 (latest stable release)                                       |
| **License**              | Apache 2.0 License                                                      |
| **Python Compatibility** | Python >=3.8                                                            |
| **Dependencies**         | None                                                                    |
| **Size**                 | nimble                                                                  |
| **Documentation**        | [WattleFlow Core Documentation](https://github.com/wattleflow/docs.git) |


# Installation
```bash

pip install wattleflow
```

# Usage examples
- [Wattleflow Workflow](https://github.com/wattleflow/workflow/)


# Dependencies
- none


# Dev guide
```bash

conda create --name core python=3.8

pip install -r requirements-dev.txt
```


# Documentation
When available, full documentation will be accessible at [WattleFlow](https://github.com/wattleflow/docs.git) documentation.


# License
WattleFlow Core is licensed under the Apache 2.0 License. See the LICENSE file for more details.
