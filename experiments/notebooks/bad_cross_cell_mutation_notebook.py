import marimo

app = marimo.App()


@app.cell
def _():
    values = [1, 2, 3]
    return (values,)


@app.cell
def _(values):
    values.append(4)
    return


if __name__ == "__main__":
    app.run()
