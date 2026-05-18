import marimo

app = marimo.App()


@app.cell
def _():
    base_values = [1, 2, 3]
    return (base_values,)


@app.cell
def _(base_values):
    extended_values = base_values + [4]
    return (extended_values,)


if __name__ == "__main__":
    app.run()
