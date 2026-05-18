import marimo
import random

app = marimo.App()


@app.cell
def _():
    sampled = random.random()
    return (sampled,)


@app.cell
def _(sampled):
    sampled
    return


if __name__ == "__main__":
    app.run()
