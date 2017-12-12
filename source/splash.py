#! /usr/bin/env python3
"""The opening screen that shows users the name of the application.

While the program loads very quickly and does not need a splash screen to make
up for slow performance, this module provides a nice introduction for users.
The provided class is designed to be used as a context manager around the code
that loads the application's resources while it is starting up."""

__author__ = 'Stephen "Zero" Chappell ' \
             '<stephen.paul.chappell@atlantis-zero.net>'
__date__ = '11 December 2017'
__version__ = 2, 6, 1
__all__ = ['Splash']

import time
import tkinter


class Splash:
    """Splash(root, file, wait) -> Splash instance"""

    __slots__ = (
        '__root', '__file', '__wait', '__window', '__canvas', '__splash'
    )

    def __init__(self, root, file, wait):
        """Initialize the Splash instance so it knows what to display."""
        self.__root = root
        self.__file = file
        self.__wait = wait + time.clock()

    def __enter__(self):
        """Display the splash screen on the display while the GUI is built."""
        # Hide the root while it is built.
        self.__root.withdraw()
        # Create components of splash screen.
        window = tkinter.Toplevel(self.__root)
        canvas = tkinter.Canvas(window)
        splash = tkinter.PhotoImage(master=window, file=self.__file)
        # Get the screen's width and height.
        scr_w = window.winfo_screenwidth()
        scr_h = window.winfo_screenheight()
        # Get the images's width and height.
        img_w = splash.width()
        img_h = splash.height()
        # Configure the window showing the logo.
        window.overrideredirect(True)
        window.geometry(f'+{scr_w - img_w >> 1}+{scr_h - img_h >> 1}')
        # Setup canvas on which image is drawn.
        canvas.configure(width=img_w, height=img_h, highlightthickness=0)
        canvas.grid()
        # Show the splash screen on the monitor.
        canvas.create_image(img_w >> 1, img_h >> 1, image=splash)
        window.update()
        # Save the variables for later cleanup.
        self.__window = window
        self.__canvas = canvas
        self.__splash = splash

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore the splash screen's parent so that it can be seen."""
        # Ensure that required time has passed.
        now = time.clock()
        if now < self.__wait:
            time.sleep(self.__wait - now)
        # Free used resources in reverse order.
        del self.__splash
        self.__canvas.destroy()
        self.__window.destroy()
        # Give control back to the root program.
        self.__root.update_idletasks()
        self.__root.deiconify()
