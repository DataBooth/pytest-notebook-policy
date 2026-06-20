import marimo
import pytest

app = marimo.App()


@pytest.fixture
def sample_values():
    return [1, 2, 3]


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
