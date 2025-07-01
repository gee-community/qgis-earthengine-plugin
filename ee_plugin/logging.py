import logging
from typing import Optional
import threading
from dataclasses import dataclass, field

from qgis.core import Qgis, QgsMessageLog, QgsFeedback

from .Map import get_iface


MODULE_NAME = __name__.split(".")[0]


@dataclass
class LocalContext:
    _state: threading.local = field(default_factory=threading.local)

    def set_feedback(self, feedback: QgsFeedback) -> None:
        self._state.feedback = feedback

    def get_feedback(self) -> Optional[QgsFeedback]:
        return getattr(self._state, "feedback", None)


local_context = LocalContext()


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
        feedback = local_context.get_feedback()
        if feedback:
            msg = self.format(record)
            if record.levelno >= logging.ERROR:
                feedback.reportError(msg, True)
            elif record.levelno >= logging.WARNING:
                feedback.pushWarning(msg)
            elif record.levelno >= logging.INFO:
                feedback.pushInfo(msg)
            elif record.levelno >= logging.DEBUG:
                feedback.pushDebugInfo(msg)
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
