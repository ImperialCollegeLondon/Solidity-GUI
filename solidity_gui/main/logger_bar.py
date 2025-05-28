import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QPlainTextEdit, QWidget


class QTextEditLogger(logging.Handler):

    class Emitter(QObject):
        log = Signal(str)

    def __init__(self, parent: QWidget):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

        # Configure the formatter
        self.setLevel(logging.INFO)
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

        # Create a QObject which will emit a signal for each log. This implicitly
        # queues each appendPlainText() call which makes it thread-safe
        self.emitter = QTextEditLogger.Emitter()
        self.emitter.log.connect(self.widget.appendPlainText)

    def emit(self, record: logging.LogRecord) -> None:
        """Add a message to the GUI handler.

        Args:
            record (str): The message to be sent.
        """
        msg = self.format(record)

        # emit a signal containing the log (emit in the Qt sense)
        self.emitter.log.emit(msg)
