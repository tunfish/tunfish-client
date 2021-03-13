# (c) 2018-2020 The Tunfish Developers
import logging
from pathlib import Path

import click

from tunfish.node.core import TunfishClient
from tunfish.node.util import setup_logging

logger = logging.getLogger(__name__)


@click.command(help="""Bootstrap and maintain connection to Tunfish network.""")
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="The configuration file",
    required=True,
)
def main(config: Path):
    setup_logging(logging.DEBUG)
    client = TunfishClient(config_file=Path(config))
    client.start_service()
