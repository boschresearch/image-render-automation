#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \cls_anyexcept.py
# Created Date: Friday, March 19th 2021, 9:03:02 am
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="Apache-2.0">
#
#   Image-Render Base Functions module
#   Copyright 2022 Robert Bosch GmbH and its subsidiaries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# </LICENSE>
###
from functools import partial
import datetime

"""this decorator may log inside a class static file all entering and leaving of functions inclusive the function depth

--- behaviour control
G_DEC_ENABLE_LOGGING (default False): the functionality can be switched on/off (but this is done normally in cmd line option --log-call )
G_DEC_LOGGING_PATH (default None): the application, that controls the execution and switches the logging functionality on
        may set the Path (as it switches the functionality on)

--- Usage:
from catharsys.decs.decorator_log import logFunctionCall

@logFunctionCall
def modObjectInSpecialWay( *args, **kwargs ):
    # do magic things
    pass | return values

additionally, some debug prints may be reasonable for longer period, but unwanted in 'release' application
this decorator offers the possibility to decorate your code with prints that can be switched on with the same cmd 
'--log-call' option

logFunctionCall.PrintLog( sMessage: str ) will write the msg into the file or it will be completly ignored, 
but nevertheless still inside your code and waits for activation

One special method is callable: LogDateTime( sApplicationName). This will print inside the log-file a status message
"""


# ###################################################################
# private attributes inside class: during import time, different code-objects will be created, and class attributes are duplicated
# !! -> global attribute works, class Attributes are not unique !!
G_DEC_LOGGING_FUNCTION_DEPTH: int = 0
G_DEC_ENABLE_LOGGING: bool = False
G_DEC_LOGGING_PATH = None


class __CLogFunctionCall:
    """this decorator class may log inside a class static file all entering and leaving of functions inclusive the function depth
    --!! it is hidden

    Access via
    --- Usage:
    from catharsys.decs.decorator_log import logFunctionCall

    @logFunctionCall
    def modObjectInSpecialWay( *args, **kwargs ):
        # do magic things
        pass | return values
    """

    # private attributes # during import time, different objects will be created, and class attributes are duplicated
    # !! -> global attribute works, class Attributes are not unique !!
    # ENABLE: bool = True
    # __FUNCTION_DEPTH: int = 0

    # ---------------------------------------------------------------------------------------
    def __init__(self, wrappedFunc):
        """forwards the __name__ and __doc__ from original function to decorator"""
        self.__name__ = wrappedFunc.__name__
        self.__doc__ = wrappedFunc.__doc__

        self.wrappedFunc = wrappedFunc
        # print(f"log Function-Calls of: {wrappedFunc.__name__}")
        pass

    # end __init__

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)

    # ---------------------------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        """the decorator itself"""
        global G_DEC_ENABLE_LOGGING
        global G_DEC_LOGGING_PATH
        if G_DEC_ENABLE_LOGGING:
            # -- logging header
            with open(G_DEC_LOGGING_PATH, "a+") as logFile:
                global G_DEC_LOGGING_FUNCTION_DEPTH

                logFile.write(
                    f"{'| '*G_DEC_LOGGING_FUNCTION_DEPTH}+ [{self.wrappedFunc.__name__}](file:\\\\{self.wrappedFunc.__code__.co_filename}#L{self.wrappedFunc.__code__.co_firstlineno})\n"
                )
                G_DEC_LOGGING_FUNCTION_DEPTH += 1
                # logFile.write(f"{'| '*self.__FUNCTION_DEPTH}+ {self.wrappedFunc.__name__}()\n")
                # self.__FUNCTION_DEPTH += 1
                logFile.flush()

            # ----------------------------------------------------------------------------------------
            retVal = self.wrappedFunc(*args, **kwargs)
            # ----------------------------------------------------------------------------------------

            # -- logging footer
            with open(G_DEC_LOGGING_PATH, "a+") as logFile:
                G_DEC_LOGGING_FUNCTION_DEPTH -= 1
                logFile.write(f"{'| '*G_DEC_LOGGING_FUNCTION_DEPTH}- {self.wrappedFunc.__name__}\n")
                # self.__FUNCTION_DEPTH -= 1
                # logFile.write(f"{'| '*self.__FUNCTION_DEPTH}- {self.wrappedFunc.__name__}\n")
                logFile.flush()
        else:
            retVal = self.wrappedFunc(*args, **kwargs)
        return retVal

    # enddef

    # ---------------------------------------------------------------------------------------
    @classmethod
    def IsEnabled(cls):
        """returns the logging state"""
        global G_DEC_ENABLE_LOGGING
        return G_DEC_ENABLE_LOGGING

    # ---------------------------------------------------------------------------------------
    @classmethod
    def LogFilePath(cls):
        """returns the logging path."""
        global G_DEC_LOGGING_PATH
        return G_DEC_LOGGING_PATH

    # enddef

    # ---------------------------------------------------------------------------------------
    @classmethod
    def PrintLog(cls, f_msg: str):
        """print some debug info for debug logging"""
        global G_DEC_ENABLE_LOGGING
        if G_DEC_ENABLE_LOGGING and isinstance(f_msg, str):
            global G_DEC_LOGGING_PATH
            # -- logging header
            with open(G_DEC_LOGGING_PATH, "a+") as logFile:
                global G_DEC_LOGGING_FUNCTION_DEPTH
                lines = [line for line in f_msg.split("\n") if line]
                for line in lines:
                    logFile.write(f"{'| '*G_DEC_LOGGING_FUNCTION_DEPTH}| {line}\n")
                logFile.flush()

        # enddef

    @classmethod
    def LogDateTime(cls, sApplication=None):
        global G_DEC_ENABLE_LOGGING

        if G_DEC_ENABLE_LOGGING:
            openMode = "a+"
            if sApplication is None:
                sApplication = "catharsys"

            global G_DEC_LOGGING_PATH
            if G_DEC_LOGGING_PATH is None:
                import os
                from pathlib import Path

                G_DEC_LOGGING_PATH = Path(os.getcwd()) / "cathy.call.md"
                openMode = "w"

            with open(G_DEC_LOGGING_PATH, openMode) as logFile:
                now = datetime.datetime.now()
                logFile.write(f"{'-'*120}\n")
                datStr = f"{sApplication}: {now.strftime('%Y-%m-%d')} @ {now.strftime('%H-%M-%S')}\n"
                logFile.write(datStr)
                logFile.write(f"{'-'*120}\n\n")
                logFile.flush()
            # endif LOGGING_PATH
        # endif ENABLE_LOGGING

    # enddef


# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------
def __disabledLogWrapper(wrapped_func, *args):
    """function prototype for none-Decorator"""
    # print(f"logging disabled. Calls won't be logged for {wrapped_func.__name__}")
    return wrapped_func


# enddef


def __disabledPrintLog(_):
    """function prototype for none-logging, the string message is completely ignored"""
    # print(f"ich erzaehle die ein Geheimnis {f_msg}")
    pass


# enddef


def __isEnabled():
    """returns the logging state. Is hidden and acessible via decorator"""
    global G_DEC_ENABLE_LOGGING
    return G_DEC_ENABLE_LOGGING


# enddef


def __LogFilePath():
    """returns the logging path. Is hidden and accesible via decorator"""
    global G_DEC_LOGGING_PATH
    return G_DEC_LOGGING_PATH


# enddef

# Need dummy argument, since the logging version of this function has one.
def __LogDateTime(_sApplication=None):
    """returns the logging path. Is hidden and accesible via decorator"""
    global G_DEC_LOGGING_PATH
    return G_DEC_LOGGING_PATH


# enddef


# builds the default decorator and logging functionality
# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------

# mirrors the decorator and disables the functionality, no runtime overhead after importing
logFunctionCall = __CLogFunctionCall
# don't use hiding, it won't work in applications with differents calls
#    like cathy calls blender
# -> makes only sense and is reliable when running in only a single application
#       logFunctionCall = __disabledLogWrapper

#       # disable the additional print
#       logFunctionCall.PrintLog = __disabledPrintLog

#       # bend hidden function to default exported decorator
#       logFunctionCall.isEnabled = __isEnabled
#       logFunctionCall.pathLogFile = __LogFilePath
#       logFunctionCall.LogDateTime = __LogDateTime


# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------
def SwitchLoggingOn(pathLogFile: str = None, sApplication: str = None):
    global G_DEC_ENABLE_LOGGING
    G_DEC_ENABLE_LOGGING = True

    if isinstance(pathLogFile, str):
        global G_DEC_LOGGING_PATH
        G_DEC_LOGGING_PATH = pathLogFile
    # endif

    global logFunctionCall
    logFunctionCall = __CLogFunctionCall
    logFunctionCall.LogDateTime(sApplication)


# end def

# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------
def SwitchLoggingOff(sApplication: str = None):
    global G_DEC_ENABLE_LOGGING
    global logFunctionCall

    if G_DEC_ENABLE_LOGGING:
        logFunctionCall.LogDateTime(sApplication)
    # endif log stop logging

    G_DEC_ENABLE_LOGGING = False

    # don't bend back functionality to wrapper function
    # disabled functionality must be capsulated in single class when
    # calling different application like cthy calls blender


# end def
