import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell
def _():
    count = 1
    count
    return (count,)


@app.cell
def _(count):
    count_1 = count + 1
    count_1
    return


if __name__ == "__main__":
    app.run()
