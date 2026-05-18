import marimo

app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    slider = mo.ui.slider(start=1, stop=10, value=5, on_change=lambda v: v)
    return (slider,)


@app.cell
def _(slider):
    slider.value
    return


if __name__ == "__main__":
    app.run()
