#! /usr/bin/env python3
"""
"""
import logging.config

import click

from quantify_proteins import CoWinner


LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "brief": {
            "format": "%(message)s"
        },
        "extended": {
            "format": "%(name)s [%(levelname)s] %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "brief",
            "level": "INFO"
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "extended",
            "filename": "app_accessions.log",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "quantify_proteins.cowinner": {
            "handlers": ["console", "file"],
            "level": "DEBUG"
        }
    }
}


@click.command()
@click.argument("config_file")
def main(config_file):
    """
    Entry point for App Accessions.

    """
    co_winner = CoWinner(config_file)
    co_winner.validate_config()
    co_winner.evaluate()
    co_winner.merge()


if __name__ == "__main__":
    logging.config.dictConfig(LOGGING_CONFIG)
    main()
