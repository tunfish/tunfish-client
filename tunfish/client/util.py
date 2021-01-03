# (c) 2018-2020 The Tunfish Developers
import logging
import sys


def setup_logging(level=logging.INFO) -> None:
    """
    Setup Python logging

    :param level:
    :return:
    """
    log_format = "%(asctime)-15s [%(name)-22s] %(levelname)-7s: %(message)s"
    logging.basicConfig(format=log_format, stream=sys.stderr, level=level)

    # logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
