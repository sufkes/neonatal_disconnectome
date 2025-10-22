import sys
import contextlib
import logging

from .logic import step1, step2

class LoggerWriter:
    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level
        self.buffer = ''

    def write(self, message):
        self.buffer += message
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            if line:
                # Use logger's internal handle method to avoid recursion
                record = self.logger.makeRecord(self.logger.name, self.level, fn='', lno=0, msg=line, args=None, exc_info=None)
                self.logger.handle(record)

    def flush(self):
        if self.buffer:
            record = self.logger.makeRecord(self.logger.name, self.level, fn='', lno=0, msg=self.buffer, args=None, exc_info=None)
            self.logger.handle(record)
            self.buffer = ''

def run_step1_with_logging(*args, **kwargs):
    logger = logging.getLogger('disconnectome')
    info_stream = LoggerWriter(logger, logging.INFO)
    error_stream = LoggerWriter(logger, logging.ERROR)

    with contextlib.redirect_stdout(info_stream), contextlib.redirect_stderr(error_stream):
        return step1(*args, **kwargs)

def run_step2_with_logging(*args, **kwargs):
    logger = logging.getLogger('disconnectome')
    info_stream = LoggerWriter(logger, logging.INFO)
    error_stream = LoggerWriter(logger, logging.ERROR)

    with contextlib.redirect_stdout(info_stream), contextlib.redirect_stderr(error_stream):
        return step2(*args, **kwargs)
