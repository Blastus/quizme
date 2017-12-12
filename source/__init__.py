#! /usr/bin/env python3
"""Initializer for the QuizMe source and starting point to understand the code.

After looking at the primary entry point for the program (QuizMe.pyw), the
reader may find this module to be the next place to understand how the program
works. This module has the QuizMe widget which represents the GUI for selecting
a testbank, loading it, and beginning a study session with the program."""

__author__ = 'Stephen "Zero" Chappell ' \
             '<stephen.paul.chappell@atlantis-zero.net>'
__date__ = '11 December 2017'
__version__ = 2, 6, 1
__all__ = ['QuizMe', 'MutableBool']

import pathlib
import test.support
import time
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import traceback
import xml.sax

from . import exe_queue, gui_logs, splash, teach_me, testbank


class QuizMe(tkinter.Frame):
    """QuizMe(master) -> QuizMe instance"""

    PROMPT = 'What testbank do you want to open?'

    @classmethod
    def main(cls):
        """Provide the primary entry point for running QuizMe."""
        with test.support.captured_output('stderr') as stderr:
            # noinspection PyPep8,PyBroadException
            try:
                tkinter.NoDefaultRoot()
                root = tkinter.Tk()
                with splash.Splash(root, 'images/QuizMe Logo.gif', 3):
                    # Set up the root window.
                    root.title('QuizMe 2.5')
                    root.resizable(False, False)
                    root.wm_iconbitmap(default='images/Icon.ico')
                    # Create the program GUI.
                    application = cls(root)
                    application.grid()
                cls.alternate_mainloop(root, 1 << 6)
            except:
                traceback.print_exc()
        cls.cleanup(stderr)

    @staticmethod
    def alternate_mainloop(root, fps):
        """Try to experimentally support threads."""
        deferred_root = exe_queue.Pipe(root)
        gui_logs.set_application_root(deferred_root)
        while True:
            try:
                root.update()
            except tkinter.TclError:
                break
            time.sleep(1 / fps)
            deferred_root.update()

    @staticmethod
    def cleanup(stream):
        """Record any errors that may have been sent to the stream."""
        value = stream.getvalue()
        if value:
            today = time.asctime()
            ruler = '=' * len(today)
            with open('error.log', 'at') as file:
                file.write(f'{ruler}\n{today}\n{ruler}\n')
                file.write(value)

    def __init__(self, master):
        """Initialize the Frame object with its widgets."""
        super().__init__(master)
        # Create every opening widget.
        self.intro = tkinter.Label(self, text=self.PROMPT)
        self.group = tkinter.LabelFrame(self, text='Filename')
        self.entry = tkinter.Entry(self.group, width=35)
        self.click = tkinter.Button(
            self.group, text='Browse ...', command=self.file
        )
        self.enter = tkinter.Button(self, text='Continue', command=self.start)
        # Make Windows entry bindings.
        self.entry.bind('<Control-Key-a>', self.select_all)
        self.entry.bind('<Control-Key-/>', lambda event: 'break')
        # Position them in this frame.
        options = dict(sticky=tkinter.NSEW, padx=5, pady=5)
        self.intro.grid(row=0, column=0, **options)
        self.group.grid(row=1, column=0, **options)
        self.entry.grid(row=0, column=0, **options)
        self.click.grid(row=0, column=1, **options)
        self.enter.grid(row=2, column=0, **options)
        self.done = False
        self.last_exit = ''
        self.next_event = iter(()).__next__

    @staticmethod
    def select_all(event):
        """Handle select all events and override their behavior."""
        event.widget.selection_range(0, tkinter.END)
        return 'break'

    def file(self):
        """Display file chooser and update the entry box appropriately."""
        filename = tkinter.filedialog.askopenfilename(
            defaultextension='.xml',
            filetypes=[('XML', '.xml'), ('All', '*')],
            initialdir=pathlib.Path.cwd() / 'tests',
            parent=self,
            title='Testbank to Open'
        )
        if filename:
            self.entry.delete(0, tkinter.END)
            self.entry.insert(0, filename)

    def start(self):
        """Validate the entry box and start the quiz engine if possible."""
        path = pathlib.Path(self.entry.get())
        if path.exists():
            if path.is_file():
                # noinspection PyPep8,PyBroadException
                try:
                    bank = testbank.BankParser.parse(str(path))
                    engine = teach_me.FAQ(bank)
                except xml.sax.SAXParseException as error:
                    tkinter.messagebox.showerror(
                        error.getMessage().title(),
                        f'Line {error.getLineNumber()}, '
                        f'Column {error.getColumnNumber()}',
                        master=self
                    )
                except RuntimeError as error:
                    tkinter.messagebox.showerror(
                        'Validation Error', error.args[0], master=self
                    )
                except:
                    tkinter.messagebox.showerror(
                        'Error', 'Unknown exception was thrown!', master=self
                    )
                    raise
                else:
                    self.done = False
                    self.next_event = iter(engine).__next__
                    self.after_idle(self.execute_quiz)
            else:
                tkinter.messagebox.showwarning(
                    'Warning', 'File does not exist.', master=self
                )
        else:
            tkinter.messagebox.showinfo(
                'Information', 'Path does not exist.', master=self
            )

    def execute_quiz(self):
        """Handle each event generated by the quiz engine with dialogs."""
        try:
            event = self.next_event()
        except StopIteration:
            if not self.done:
                raise RuntimeError('Final event not processed!')
        else:
            if isinstance(event, teach_me.Enter):
                gui_logs.ShowStatus(self, 'Entering', event, self.execute_quiz)
            elif isinstance(event, teach_me.Exit):
                gui_logs.ShowStatus(self, 'Exiting', event, self.execute_quiz)
                self.last_exit = event.kind
            elif isinstance(event, teach_me.Question):
                gui_logs.AskQuestion(self, event, self.execute_quiz)
            elif isinstance(event, teach_me.Report):
                continue_after_review = MutableBool(True)
                if self.last_exit == 'Section' and event.wrong:
                    continue_after_review.value = False
                    gui_logs.ReviewProblems(self, event, continue_after_review)
                if continue_after_review.value:
                    gui_logs.ShowReport(self, event, self.execute_quiz)
                if event.final:
                    tkinter.messagebox.showinfo(
                        'Congratulations!',
                        'You have finished the test.',
                        master=self
                    )
                    self.done = True
            else:
                tkinter.messagebox.showerror(
                    'Type Error', repr(event), master=self
                )


# noinspection PyAttributeOutsideInit
class MutableBool:
    """MutableBool(value) -> MutableBool instance"""

    __slots__ = '__value'

    def __init__(self, value=None):
        """Initialize the value of the mutable boolean."""
        self.value = value

    def get_value(self):
        """Get the value of the mutable boolean."""
        return self.__value

    def set_value(self, value):
        """Set the value of the mutable boolean."""
        self.__value = bool(value)

    value = property(get_value, set_value, doc='Value of the mutable boolean.')
