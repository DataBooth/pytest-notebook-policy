import marimo

app = marimo.App()


@app.cell
def _():
    items = [1, 2]
    return (items,)


@app.cell
def _(items):
    items.append(3)
    return


if __name__ == "__main__":
    app.run()
