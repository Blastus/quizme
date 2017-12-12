#! /usr/bin/env python3
"""Entry point for the QuizMe automated quizzing/testing program.

This program is designed to make quizzing and testing for the purpose of
studying easy for the user. This file is meant to act as the main entry
point to start the application and simply accesses the main source files
to do so. If you want to help make a test editor, please let me know!"""

__author__ = 'Stephen "Zero" Chappell ' \
             '<stephen.paul.chappell@atlantis-zero.net>'
__date__ = '11 December 2017'
__version__ = 2, 6, 1

import source  # Access the source ...

source.QuizMe.main()  # and execute main.
