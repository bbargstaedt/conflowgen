import datetime
import logging
import os
import sys

logs_root_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    os.pardir,
    "data",
    "logs"
)


def setup_logger() -> logging.Logger:
    time_prefix = str(datetime.datetime.now()).replace(":", "-").replace(" ", "--").split(".", maxsplit=1)[0]
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt="%d.%m.%Y %H:%M:%S %z"
    )

    logger = logging.getLogger("conflowgen")
    logger.setLevel(logging.DEBUG)

    flow_handler = logging.StreamHandler(stream=sys.stdout)
    flow_handler.setLevel(logging.DEBUG)
    flow_handler.setFormatter(formatter)
    logger.addHandler(flow_handler)

    file_handler = logging.FileHandler(
        os.path.join(
            logs_root_dir,
            time_prefix + ".log"
        )
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger
