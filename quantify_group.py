#! /usr/bin/env python3

import click

from quantify_proteins import Quantifier


@click.command()
@click.argument("config_file")
def main(config_file: str):
    """
    """
    quantifier = Quantifier(config_file)
    quantifier.quantify_group()


if __name__ == "__main__":
    main()
