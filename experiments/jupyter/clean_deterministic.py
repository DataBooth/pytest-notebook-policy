import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell
def _():
    values = [1, 2, 3]
    values
    return (values,)


@app.cell
def _(values):
    doubled = [value * 2 for value in values]
    doubled
    return


if __name__ == "__main__":
    app.run()
