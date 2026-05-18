import marimo

app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    seed_values = [1, 2, 3]
    return (seed_values,)


@app.cell
def _(seed_values):
    enriched_values = seed_values + [4]
    return (enriched_values,)


@app.cell
def _(enriched_values, mo):
    mo.md(f"Values: {enriched_values}")
    return


if __name__ == "__main__":
    app.run()
