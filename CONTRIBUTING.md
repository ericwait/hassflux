# Contributing to Hassflux

First off, thank you for considering contributing to Hassflux! It's people like you that make it a better tool for the Home Assistant community.

## How Can I Contribute?

### Reporting Bugs
*   Check the [GitHub Issues](https://github.com/ericwait/hassflux/issues) to see if the bug has already been reported.
*   If not, open a new issue. Include a clear title, a detailed description, and steps to reproduce the behavior.

### Suggesting Enhancements
*   Open a new issue with the tag "enhancement".
*   Describe the current limitation and how your suggestion would improve the tool.

### Pull Requests
1.  **Fork** the repository and create your branch from `main`.
2.  **Install** the development dependencies:
    ```bash
    pip install -e ".[dev]"
    ```
3.  **Implement** your changes.
4.  **Lint and Type Check** your code:
    ```bash
    ruff check src/
    mypy src/
    ```
5.  **Write Tests** if applicable.
6.  **Submit** your pull request!

## Development Environment

We recommend using a virtual environment or a Conda/Mamba environment:

```bash
# Using Mamba
mamba env create -f environment.yml
mamba activate influx-migrate
pip install -e ".[dev]"
```

## Coding Standards

*   **Style:** We use `ruff` for linting and formatting.
*   **Types:** We use `mypy` for static type checking. All new functions should have type hints.
*   **CLI:** New features should be integrated into the Typer CLI in `src/hassflux/cli.py` or `src/hassflux/tools.py`.

## License

By contributing, you agree that your contributions will be licensed under its [MIT License](LICENSE).
