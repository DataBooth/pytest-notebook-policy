import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell
def _():
    import random
    items = [1, 2, 3]
    items
    return items, random


@app.cell
def _(items, random):
    items.append(random.randint(1, 10))
    items
    return


if __name__ == "__main__":
    app.run()
