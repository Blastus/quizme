#! /usr/bin/env python3
"""Experimental support for threads in a tkinter application.

Though never used for its intended purpose, this module is used with an
alternative mainloop in the application in the hopes to enable threads to be
easily used without causing problems. This was written before the Safe Tkinter
modules were written and could probably be completely replaced by them."""

__author__ = 'Stephen "Zero" Chappell ' \
             '<stephen.paul.chappell@atlantis-zero.net>'
__date__ = '11 December 2017'
__version__ = 2, 6, 1
__all__ = ['Pipe', 'DeferredCall']

import collections
import queue


class Pipe:
    """Pipe(obj) -> Pipe instance"""

    __slots__ = '__obj', '__queue', '__dict__'

    def __init__(self, obj):
        """Initialize Pipe object so it can capture method calls."""
        self.__obj = obj
        self.__queue = queue.Queue()

    def __getattr__(self, name):
        """Generate methods on the fly and cache the results."""
        method = _Method(self.__queue, name)
        setattr(self, name, method)
        return method

    def update(self):
        """Execute all methods calls since update was last ran."""
        while not self.__queue.empty():
            name, args, kwargs = self.__queue.get()
            getattr(self.__obj, name)(*args, **kwargs)


# Create class that stores all the details to run a function or method later.
DeferredCall = collections.namedtuple('DeferredCall', 'method, args, kwargs')


class _Method:
    """_Method(todo) -> _Method instance"""

    __slots__ = '__todo', '__name'

    def __init__(self, todo, name):
        """Initialize the virtual method so calls can be recorded."""
        self.__todo = todo
        self.__name = name

    def __call__(self, *args, **kwargs):
        """Record the call so that it may be executed later on."""
        self.__todo.put(DeferredCall(self.__name, args, kwargs))
