from logging.config import dictConfig

from social.config import DevConfig, config


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "format": "%(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ | %(levelname)-8s | %(name)s:%(lineno)-4d | %(message)s",  # noqa: E501
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "social.log",
                    "maxBytes": 1024 * 1024 * 5,  # 5 MB
                    "backupCount": 5,
                    "encoding": "utf8",
                },
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default", "rotating_file"],
                    "level": "INFO",
                },
                "social": {
                    "handlers": ["default"],
                    "level": "DEBUG"
                    if isinstance(config, DevConfig)
                    else "INFO",
                    "propagate": False,  # Prevents double logging sent to root logger
                },
                "databases": {
                    "handlers": ["default"],
                    "level": "WARNING",
                },
                "fastapi": {
                    "handlers": ["default"],
                    "level": "WARNING",
                    "propagate": False,
                },
                "aiosqlite": {
                    "handlers": ["default"],
                    "level": "WARNING",
                },
            },
        }
    )
