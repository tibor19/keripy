# -*- encoding: utf-8 -*-
"""
keri.app.configing module

"""
import json
import os

import cbor2 as cbor
import hjson
import msgpack
from hio.base import filing, doing

from .. import help

logger = help.ogler.getLogger()


def openCF(cls=None, filed=True, **kwa):
    """
    Returns contextmanager generated by openFiler with Configer instance as default
    and filed = True
    """
    if cls == None:  # can't reference class before its defined below
        cls = Configer
    return filing.openFiler(cls=cls, filed=True, **kwa)


class Configer(filing.Filer):
    """
    Habitat Config File

    Supports four serializations. HJSON, JSON, MGPK (MsgPack), and CBOR
    The serialization is determined by the file extension .fext which may be
    either '.json', '.mgpk', or '.cbor'.  The default is that .json extension
    uses HJSON because HJSON can get (load) a strict json file.
    To use strict json on put (dump) then set .human to false.

    See https://github.com/hjson/hjson-py

    Attributes:  (see Filer for inherited attributes)
        human (bool): True (default) means use human friendly HJSON when fext is JSON
    """
    TailDirPath = "keri/cf"
    CleanTailDirPath = "keri/clean/cf"
    AltTailDirPath = ".keri/cf"
    AltCleanTailDirPath = ".keri/clean/cf"
    TempPrefix = "keri_cf_"

    def __init__(self, name="conf", base="main", filed=True, mode="r+b",
                 fext="json", human=True, **kwa):
        """
        Setup config file .file at .path

        Parameters:
            name (str): directory path name differentiator directory/file
                When system employs more than one keri installation, name allows
                differentiating each instance by name
            base (str): optional directory path segment inserted before name
                that allows further differentiation with a hierarchy. "" means
                optional.
            temp (bool): assign to .temp
                True then open in temporary directory, clear on close
                Otherwise then open persistent directory, do not clear on close
            headDirPath (str): optional head directory pathname for main database
                Default .HeadDirPath
            perm (int): optional numeric os dir permissions for database
                directory and database files. Default .DirMode
            reopen (bool): True means (re)opened by this init
                           False  means not (re)opened by this init but later
            clear (bool): True means remove directory upon close if reopon
                          False means do not remove directory upon close if reopen
            reuse (bool): True means reuse self.path if already exists
                          False means do not reuse but remake self.path
            clean (bool): True means path uses clean tail variant
                             False means path uses normal tail variant
            filed (bool): True means .path is file path not directory path
                          False means .path is directory path not file path
            mode (str): File open mode when filed default non-truncate r+w
            fext (str): File extension when filed
            human(bool): True means use human friendly HJSON when fext is json

        """
        super(Configer, self).__init__(name=name,
                                       base=base,
                                       filed=filed,
                                       mode=mode,
                                       fext=fext,
                                       **kwa)
        self.human = True if human else False


    def put(self, data: dict, human=None):
        """
        Serialize data dict and write to file given by .path where serialization is
        given by .fext path's extension of either JSON, MsgPack, or CBOR for extension
        .json, .mgpk, or .cbor respectively

        Parameters:
            data (dict): to be serialized per file extension on .path

        Raises:
            IOError if unsupported file extension
        """
        if not self.file or self.file.closed:
            raise ValueError(f"File '{self.path}' not opened.")

        human = human if human is not None else self.human
        self.file.seek(0)
        self.file.truncate()
        root, ext = os.path.splitext(self.path)
        if ext == '.json':  # json can't dump to binary
            if human:
                ser = hjson.dumps(data)
            else:
                ser = json.dumps(data, indent=2)
            ser = ser.encode("utf-8")
        elif ext == '.mgpk':
            ser = msgpack.dumps(data)
        elif ext == '.cbor':
            ser = cbor.dumps(data)
        else:
            raise IOError(f"Invalid file path ext '{ext}' "
                          f"not '.json', '.mgpk', or 'cbor'.")
        self.file.write(ser)
        self.file.flush()
        os.fsync(self.file.fileno())
        return True


    def get(self, human=None):
        """
        Returns:
            data (dict): converted from contents of file path given extention
                         empty dict if empty file

        Raises:
            IOError if unsupported file extension

        file may be either json, msgpack, or cbor given by extension .json, .mgpk, or
        .cbor respectively

        """
        if not self.file or self.file.closed:
            raise ValueError(f"File '{self.path}' not opened.")

        human = human if human is not None else self.human
        it = {}
        self.file.seek(0)
        ser = self.file.read()
        if ser:  # not empty
            root, ext = os.path.splitext(self.path)
            if ext == '.json':  # json.load works with bytes as well as str
                if human:
                    it = hjson.loads(ser.decode("utf-8"))
                else:
                    it = json.loads(ser.decode("utf-8"))
            elif ext == '.mgpk':
                it = msgpack.loads(ser)
            elif ext == '.cbor':
                it = cbor.loads(ser)
            else:
                raise IOError(f"Invalid file path ext '{ext}' "
                             f"not '.json', '.mgpk', or 'cbor'.")
        return it


class ConfigerDoer(doing.Doer):
    """
    Basic Filer Doer

    Attributes:
        done (bool): completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        configer (Configer): instance

    Properties:
        tyme (float): relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        tymth (func): closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        tock (float)): desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    """

    def __init__(self, configer, **kwa):
        """
        Parameters:
           tymist (Tymist): instance
           tock (float): initial value of .tock in seconds
           configer (Configer): instance
        """
        super(ConfigerDoer, self).__init__(**kwa)
        self.configer = configer

    def enter(self):
        """"""
        if not self.configer.opened:
            self.configer.reopen()

    def exit(self):
        """"""
        self.configer.close(clear=self.configer.temp)
