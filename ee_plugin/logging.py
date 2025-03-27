import logging

from .feedback_context import get_feedback
from qgis.core import Qgis, QgsMessageLog

from .Map import get_iface


MODULE_NAME = __name__.split(".")[0]


class QGISMessageLogHandler(logging.Handler):
    """
    Handler that routes Python logging messages to the QGIS Message Log.
    """

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        super().__init__()

    def emit(self, record):
        """
        Overridden method from logging.Handler:
        Called with a LogRecord whenever a new log message is issued.
        """
        notify_user = False
        if record.levelno >= logging.ERROR:
            qgis_level = Qgis.Critical
            notify_user = True
        elif record.levelno >= logging.WARNING:
            qgis_level = Qgis.Warning
        else:
            # INFO, DEBUG, etc. can map to Qgis.Info
            qgis_level = Qgis.Info

        # Format the log message
        msg = self.format(record)

        # Actually write the message to the QGIS Message Log
        QgsMessageLog.logMessage(
            message=msg,
            tag=self.plugin_name,
            level=qgis_level,
            notifyUser=notify_user,
        )

        # Also push the message to the QGIS Processing Feedback
        feedback = get_feedback()
        if feedback:
            msg = self.format(record)
            if record.levelno >= logging.WARNING:
                feedback.pushWarning(msg)
            else:
                feedback.pushInfo(msg)


class QGISMessageBarHandler(logging.Handler):
    """
    Handler that routes Python logging messages to the QGIS Message Bar.
    """

    def __init__(self, plugin_name: str, duration: int = 0):
        self.plugin_name = plugin_name
        self.duration = duration
        super().__init__()

    def emit(self, record):
        # Map Python log levels to QGIS message bar levels
        if record.levelno >= logging.ERROR:
            qgis_level = Qgis.Critical
        elif record.levelno >= logging.WARNING:
            qgis_level = Qgis.Warning
        else:
            # TODO: Support Qgis.Success for positive messages?
            qgis_level = Qgis.Info

        # Format the log message
        msg = self.format(record)

        # Push the message to the QGIS Message Bar
        iface = get_iface()
        if iface and iface.messageBar():
            try:
                iface.messageBar().pushMessage(
                    f"{self.plugin_name}",
                    msg,
                    level=qgis_level,
                    duration=self.duration,
                )
            except Exception as e:
                # If we can't push the message, log it to the QGIS Message Log
                QgsMessageLog.logMessage(
                    message=f"Error pushing message to QGIS Message Bar: {str(e)}",
                    tag=self.plugin_name,
                    level=Qgis.Critical,
                    notifyUser=True,
                )


class QGISFeedbackHandler(logging.Handler):
    """Sends logs to the active processing feedback, if available."""

    def emit(self, record):
        feedback = get_feedback()
        if feedback:
            msg = self.format(record)
            if record.levelno >= logging.WARNING:
                feedback.pushWarning(msg)
            else:
                feedback.pushInfo(msg)


def setup_logger(plugin_name: str, logger_name: str = MODULE_NAME) -> None:
    """Configure and return a logger for your QGIS Plugin."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    qgis_log_handler = QGISMessageLogHandler(plugin_name=plugin_name)
    qgis_log_handler.setLevel(logging.INFO)
    qgis_log_handler.setFormatter(
        logging.Formatter("%(levelname)s: %(name)s - %(message)s")
    )
    logger.addHandler(qgis_log_handler)

    qgis_bar_handler = QGISMessageBarHandler(plugin_name=plugin_name, duration=5)
    qgis_bar_handler.setLevel(logging.WARNING)
    qgis_bar_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(qgis_bar_handler)

    feedback_handler = QGISFeedbackHandler()
    feedback_handler.setLevel(logging.INFO)
    feedback_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(feedback_handler)


def teardown_logger(logger_name: str = MODULE_NAME) -> None:
    """Remove all handlers from the logger to clean up resources."""
    logger = logging.getLogger(logger_name)
    # Copy the list to avoid modification during iteration
    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
