import logging
import logging.config


def _setup_logging():
    log_config = {"version": 1, "root": {"level": "INFO"}}
    logging.config.dictConfig(log_config)


_setup_logging()
