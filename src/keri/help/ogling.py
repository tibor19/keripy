# -*- encoding: utf-8 -*-
"""
keri.help.logging module

"""
import os
import logging
import tempfile
import shutil


class Oglery():
    """
    Olgery instances are logger factories that configure and build loggers
    Only need one Oglery per application

    logging.getLogger(name). Multiple calls to getLogger() with the same name
    will always return a reference to the same Logger object.

    Attributes:
        .level is logging severity level
        .logFilePath is path to log file
    """
    HeadDirPath = "/var"  # default in /var
    TailDirPath = "keri/log"
    AltHeadDirPath = "~"  #  put in ~ when /var not permitted
    AltTailDirPath = ".keri/log"

    def __init__(self, name='main', level=logging.ERROR, file=False, temp=False,
                 headDirPath=None):
        """
        Init Loggery factory instance

        Parameters:
            name is application specific log file name
            level is int logging level from logging. Higher is more restrictive.
                This sets the level of the baseLogger relative to the global level
                logs output if severity level is at or above set level.

                Level    Numeric value
                CRITICAL 50
                ERROR    40
                WARNING  30
                INFO     20
                DEBUG    10
                NOTSET    0
            file is Boolean True means create logfile Otherwise not
            temp is Boolean If file then True means use temp direction
                                         Otherwise use  headDirpath
            headDirPath is str for custom headDirPath for log file

        """
        self.name = name
        self.level = level  # basic logger level
        self.path = None
        self.file = True if file else False
        self.temp = True if temp else False

        if self.file:
            if self.temp:
                headDirPath = tempfile.mkdtemp(prefix="keri_log_", suffix="_test", dir="/tmp")
                self.path = os.path.abspath(
                                    os.path.join(headDirPath,
                                                 self.TailDirPath))
                os.makedirs(self.path)

            else:
                if not headDirPath:
                    headDirPath = self.HeadDirPath

                self.path = os.path.abspath(
                                    os.path.expanduser(
                                        os.path.join(headDirPath,
                                                     self.TailDirPath)))

                if not os.path.exists(self.path):
                    try:
                        os.makedirs(self.path)
                    except OSError as ex:
                        headDirPath = self.AltHeadDirPath
                        self.path = os.path.abspath(
                                            os.path.expanduser(
                                                os.path.join(headDirPath,
                                                             self.AltTailDirPath)))
                        if not os.path.exists(self.path):
                            os.makedirs(self.path)
                else:
                    if not os.access(self.path, os.R_OK | os.W_OK):
                        headDirPath = self.AltHeadDirPath
                        self.path = os.path.abspath(
                                            os.path.expanduser(
                                                os.path.join(headDirPath,
                                                             self.AltTailDirPath)))
                        if not os.path.exists(self.path):
                            os.makedirs(self.path)

            fileName = "{}.log".format(self.name)
            self.path = os.path.join(self.path, fileName)

        #create formatters
        self.baseFormatter = logging.Formatter('%(message)s')  # basic format
        self.failFormatter = logging.Formatter('***Fail: %(message)s')  # failure format

        #create handlers and formatters
        self.baseConsoleHandler = logging.StreamHandler()  # sys.stderr
        self.baseConsoleHandler.setFormatter(self.baseFormatter)
        self.failConsoleHandler = logging.StreamHandler()  # sys.stderr
        self.failConsoleHandler.setFormatter(self.failFormatter)

        if self.path:  # if empty then no handlers so no logging to file
            self.baseFileHandler = logging.FileHandler(self.path)
            self.baseFileHandler.setFormatter(self.baseFormatter)
            self.failFileHandler = logging.FileHandler(self.path)
            self.failFileHandler.setFormatter(self.failFormatter)


    def clearDirPath(self):
        """
        Remove logfile directory at .path
        """
        if os.path.exists(self.path):
            shutil.rmtree(os.path.dirname(self.path))


    def getBlogger(self, name=__name__, level=None):
        """
        Returns Basic Logger
        default is to name logger after module
        """
        blogger = logging.getLogger(name)
        blogger.propagate = False  # disable propagation of events
        if level is not None:
            self.level = level
        blogger.setLevel(self.level)
        blogger.addHandler(self.baseConsoleHandler)
        if self.path:
            blogger.addHandler(self.baseFileHandler)
        return blogger

    def getFlogger(self, name=__name__):
        """
        Returns Failure Logger
        Since loggers are singletons by name we have to use unique name if
            we want to use different log format so we append .fail to base name
        """
        # Since loggers are singletons by name we have to change name if we
        # want to use different log format
        flogger = logging.getLogger("%s.%s" % (name, 'fail'))
        flogger.propagate = False  # disable propagation of events
        flogger.setLevel(logging.ERROR)
        flogger.addHandler(self.failConsoleHandler)  # output to console
        if self.path:
            flogger.addHandler(self.failFileHandler)  # output to file
        return flogger

    def getLoggers(self, name=__name__):
        """
        Returns duple (blogger, flogger) of basic and failure loggers
        """
        return (self.getBlogger(name), self.getFlogger(name))

