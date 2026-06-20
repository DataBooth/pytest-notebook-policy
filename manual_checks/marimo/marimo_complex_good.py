# Source: https://raw.githubusercontent.com/marimo-team/gallery-examples/main/notebooks/math/matrix.py
import marimo

__generated_with = "0.20.2"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    import numpy as np


@app.cell
def _():
    matrix = mo.ui.matrix(np.eye(3))
    matrix
    return (matrix,)


@app.cell
def _(matrix):
    np.asarray(matrix.value)
    return
