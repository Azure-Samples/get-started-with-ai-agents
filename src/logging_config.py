# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.

import logging
import sys
from typing import Optional

def configure_logging(log_file_name: Optional[str] = None, logger_name: str = "azureaiapp") -> logging.Logger:
    """
    Configure and return a logger with both stream (stdout) and optional file handlers.

    :param log_file_name: The path to the log file. If provided, logs will also be written to this file.
    :type log_file_name: Optional[str]
    :param logger_name: The name of the logger to configure.
    :type logger_name: str
    :return: The configured logger instance.
    :rtype: logging.Logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Stream handler (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    # File handler if a log file is specified
    if log_file_name:
        file_handler = logging.FileHandler(log_file_name)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger