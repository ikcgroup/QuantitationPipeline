#! /usr/bin/env python3
"""
This script is designed to apply a patched formula to the benchmarking
outputs for the quantitation tool. A bug exists in the calculations in these
spreadsheets due to a hardcoded formula MEDIAN($H$2:$H$740) in the C# version
of the quantitation pipeline.

This script therefore modifies this formula according to the real number of rows
in the spreadsheet and then writes out the result to an _FIXED file, which
should be used as the benchmark in the tests.

"""

import os

import click
import openpyxl
import xlwings as xw


@click.command()
@click.argument("benchmark_file")
def fix_benchmark_spreadsheet(benchmark_file: str):
    """
    Applies the above described formula fix to the benchmark_file.

    """
    book = openpyxl.load_workbook(benchmark_file)
    sheet = book["Protein"]
    sheet["P2"] = f"=MEDIAN($H$2:$H${sheet.max_row})"
    fixed_file = benchmark_file.replace(".xlsx", "_FIXED.xlsx")
    book.save(fixed_file)
    app = xw.App(visible=False)
    book = app.api.open_workbook(workbook_file_name=os.path.abspath(fixed_file),
                                 timeout=3000)
    book.save()
    app.kill()


if __name__ == "__main__":
    fix_benchmark_spreadsheet()
