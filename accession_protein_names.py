#! /usr/bin/env python3

import click

from quantify_proteins import Accessions


@click.command()
@click.argument("config_file")
def main(config_file: str):
    """
    """
    accessions = Accessions(config_file)
    accessions.merge_protein_names()


if __name__ == "__main__":
    main()
