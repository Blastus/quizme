#! /usr/bin/env python3
"""Supplier of supplemental GUI elements used in the application.

The name of this module is a corruption of "dialog" and references the fact
that all custom widgets in this program have the same nature. If any of the
visual elements that deal directly with taking a test need to be modified,
this module most certainly is the place to make the needed modifications."""

__author__ = 'Stephen "Zero" Chappell ' \
             '<stephen.paul.chappell@atlantis-zero.net>'
__date__ = '11 December 2017'
__version__ = 2, 6, 1
__all__ = [
    'set_application_root',
    'get_application_root',
    'ShowStatus',
    'AskQuestion',
    'ReviewProblems',
    'ShowReport'
]

import abc
import functools
import textwrap
import tkinter
import tkinter.font
import tkinter.messagebox
import tkinter.simpledialog
from tkinter.constants import *

from . import exe_queue

_APPLICATION_ROOT = None


def set_application_root(root):
    """Store the application root for use by dialogs in this module."""
    global _APPLICATION_ROOT
    if not isinstance(root, (tkinter.Tk, exe_queue.Pipe)):
        raise TypeError('application root is not of an acceptable type')
    _APPLICATION_ROOT = root


def get_application_root():
    """Allow dialogs to get the application root to make calls as needed."""
    if _APPLICATION_ROOT is None:
        raise ValueError('application root has not been properly set')
    return _APPLICATION_ROOT


class _Dialog(tkinter.simpledialog.Dialog, metaclass=abc.ABCMeta):
    """Abstract Base Class"""

    TITLE_SIZE = 16
    TEXT_WIDTH = 40

    @abc.abstractmethod
    def __init__(self, parent, title):
        """Make _Dialog instances impossible to create directly."""
        super().__init__(parent, title)

    def ok(self, event=None):
        """Apply changes dialog wants to make and force its closure."""
        self.withdraw()
        self.update_idletasks()
        try:
            self.apply()
        finally:
            self.cancel(force=True)

    def cancel(self, event=None, force=False):
        """Verify the user wants to close the dialog before disappearing."""
        if force or tkinter.messagebox.askyesno(
                'Warning',
                'Are you sure you want\nto stop taking this test?',
                master=self
        ):
            if self.parent is not None:
                self.parent.focus_set()
            self.destroy()


# noinspection PyAttributeOutsideInit
class ShowStatus(_Dialog):
    """ShowStatus(parent, title, message, callback) -> ShowStatus instance"""

    WAIT = 3

    def __init__(self, parent, title, message, callback):
        """Initialize the dialog with a message and callback."""
        self.message = message
        self.callback = callback
        super().__init__(parent, title)

    def body(self, master):
        """Display the message in the dialog with a certain font size."""
        style = tkinter.font.Font(self, size=self.TITLE_SIZE)
        self.status = tkinter.Label(master, text=self.message, font=style)
        self.status.grid(
            sticky=NSEW, padx=self.TITLE_SIZE, pady=self.TITLE_SIZE
        )
        return self.status

    def buttonbox(self):
        """Automatically proceed to the next stage after one second."""
        self.after(self.WAIT * 1000, self.ok)

    def apply(self):
        """Run the callback when possible to continue with the process."""
        get_application_root().after_idle(self.callback)


class AskQuestion(_Dialog):
    """AskQuestion(parent, event, callback) -> AskQuestion instance"""

    def __init__(self, parent, event, callback):
        """Initialize the dialog with information taken from the event."""
        self.question = textwrap.wrap(event.question, self.TEXT_WIDTH)
        self.choices = event.choices
        self.give_answer = event.answer
        self.callback = callback
        self.buttons = []
        self.labels = []
        super().__init__(parent, event.category)

    def body(self, master):
        """Display each line of the question in the body area."""
        for line in self.question:
            self.labels.append(tkinter.Label(master, text=line, justify=LEFT))
            self.labels[-1].grid(sticky=NSEW)

    def buttonbox(self):
        """Build the buttonbox with all available answers to choose from."""
        box = tkinter.Frame(self)
        for choice in self.choices:
            self.buttons.append(tkinter.Button(
                box,
                text=textwrap.fill(choice, self.TEXT_WIDTH),
                width=self.TEXT_WIDTH,
                command=functools.partial(self.click, choice)
            ))
            self.buttons[-1].grid(padx=5, pady=5)
        box.pack()

    def click(self, choice):
        """Record the answer corresponding with the user's clicked button."""
        self.give_answer(choice)
        self.ok()

    def apply(self):
        """Ask the application's root to run the callback when possible."""
        get_application_root().after_idle(self.callback)


# noinspection PyAttributeOutsideInit
class ReviewProblems(_Dialog):
    """ReviewProblems(parent, event, flag) -> ReviewProblems instance"""

    def __init__(self, parent, event, continue_after_review):
        """Initialize the report with problems generated by the event."""
        self.problems = list(event.get_problems())
        self.problem = 0
        self.continue_after_review = continue_after_review
        super().__init__(parent, 'Problems')

    def body(self, master):
        """Build the body with a display to review wrong answers."""
        title = tkinter.font.Font(self, size=self.TITLE_SIZE)
        legend = tkinter.font.Font(self, weight='bold')
        # Create display variables.
        self.category = tkinter.StringVar(master)
        self.question = tkinter.StringVar(master)
        self.answer = tkinter.StringVar(master)
        self.right = tkinter.StringVar(master)
        # Create form labels.
        self.c_label = tkinter.Label(
            master, textvariable=self.category, font=title
        )
        self.q_label = tkinter.Label(master, textvariable=self.question)
        self.you_answered = tkinter.Label(
            master, text='You answered:', font=legend
        )
        self.a_label = tkinter.Label(master, textvariable=self.answer)
        self.right_answer = tkinter.Label(
            master, text='Right answer:', font=legend
        )
        self.r_label = tkinter.Label(master, textvariable=self.right)
        # Create control buttons.
        self.back = tkinter.Button(
            master,
            text='< < <',
            width=self.TEXT_WIDTH >> 1,
            command=self.go_back
        )
        self.next = tkinter.Button(
            master,
            text='> > >',
            width=self.TEXT_WIDTH >> 1,
            command=self.go_next
        )
        # Display the body.
        options = dict(sticky=NSEW, padx=5, pady=5)
        self.c_label.grid(row=0, column=0, columnspan=2, **options)
        self.q_label.grid(row=1, column=0, columnspan=2, **options)
        self.you_answered.grid(row=2, column=0, **options)
        self.a_label.grid(row=2, column=1, **options)
        self.right_answer.grid(row=3, column=0, **options)
        self.r_label.grid(row=3, column=1, **options)
        self.back.grid(row=4, column=0, **options)
        self.next.grid(row=4, column=1, **options)
        # Update the labels.
        self.update()

    def go_back(self):
        """Return to a previous problem being reviewed."""
        self.problem -= 1
        self.update()

    def go_next(self):
        """Proceed to another question that was answered incorrectly."""
        self.problem += 1
        self.update()

    def update(self):
        """Update the labels and button states based the review's state."""
        p_index, p_array = self.problem, self.problems
        problem = p_array[p_index]
        self.category.set(problem.category)
        self.question.set(textwrap.fill(problem.question, self.TEXT_WIDTH))
        self.answer.set(textwrap.fill(problem.answer, self.TEXT_WIDTH >> 1))
        self.right.set(textwrap.fill(problem.right, self.TEXT_WIDTH >> 1))
        # Update the buttons.
        self.back['state'] = NORMAL if p_index > 0 else DISABLED
        self.next['state'] = NORMAL if p_index + 1 < len(p_array) else DISABLED

    def apply(self):
        """Signal the quiz engine to continue processing after the review."""
        self.continue_after_review.value = True


# noinspection PyAttributeOutsideInit
class ShowReport(_Dialog):
    """ShowReport(parent, event, callback) -> ShowReport instance"""

    RULE = '='

    def __init__(self, parent, event, callback):
        """Initialize the report dialog with information from the event."""
        self.level = event.level
        self.right = event.right
        self.wrong = event.wrong
        self.total = event.total
        self.callback = callback
        super().__init__(parent, 'Report')

    def body(self, master):
        """Build the body with information from the generating event."""
        title = tkinter.font.Font(self, size=self.TITLE_SIZE)
        legend = {'anchor': W,
                  'justify': LEFT,
                  'font': tkinter.font.Font(self, weight='bold')}
        # Create all labels.
        text = f'Cumulative score for\nprevious {self.level}:'
        self.explanation = tkinter.Label(master, text=text, font=title)
        self.ruler_one = tkinter.Label(
            master, text=self.RULE * self.TEXT_WIDTH
        )
        self.answers_right = tkinter.Label(
            master, text='Answers right:', **legend
        )
        self.display_right = tkinter.Label(master, text=str(self.right))
        self.answers_wrong = tkinter.Label(
            master, text='Answers wrong:', **legend
        )
        self.display_wrong = tkinter.Label(master, text=str(self.wrong))
        self.percent = tkinter.Label(
            master, text='Percentage correct:', **legend
        )
        percentage = str(int(100 * self.right / self.total + 0.5)) + '%'
        self.display = tkinter.Label(master, text=percentage)
        self.ruler_two = tkinter.Label(
            master, text=self.RULE * self.TEXT_WIDTH
        )
        # Display the results.
        options = dict(sticky=NSEW, padx=5, pady=5)
        self.explanation.grid(row=0, column=0, columnspan=2, **options)
        self.ruler_one.grid(row=1, column=0, columnspan=2, **options)
        self.answers_right.grid(row=2, column=0, **options)
        self.display_right.grid(row=2, column=1, **options)
        self.answers_wrong.grid(row=3, column=0, **options)
        self.display_wrong.grid(row=3, column=1, **options)
        self.percent.grid(row=4, column=0, **options)
        self.display.grid(row=4, column=1, **options)
        self.ruler_two.grid(row=5, column=0, columnspan=2, **options)

    def apply(self):
        """Have the application's root continue with the callback ASAP."""
        get_application_root().after_idle(self.callback)
