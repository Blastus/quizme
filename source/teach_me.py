#! /usr/bin/env python3
"""Events and event generator for a quizzing or testing session.

The FAQ class is an iterator that takes a testbank and generates the events
that control the flow of how quizzes and tests are taken. Reports are
automatically generated along the way and keep track of the user's progress.
The __init__ module is entirely dependent on this code to know what to do."""

__author__ = 'Stephen "Zero" Chappell ' \
             '<stephen.paul.chappell@atlantis-zero.net>'
__date__ = '11 December 2017'
__version__ = 2, 6, 1
__all__ = ['FAQ', 'Enter', 'Exit', 'Report', 'Question', 'Answer']

import abc
import random

from . import quizcore


class FAQ:
    """FAQ(testbank) -> FAQ instance"""

    __slots__ = 'test'

    def __init__(self, testbank):
        """Initialize the FAQ instance with a UnitTest it can use."""
        self.test = quizcore.UnitTest(testbank)

    def __iter__(self):
        """Generate events that represent the examination session."""
        unittest = self.test
        yield Enter(unittest)
        unittest_report = Report(unittest)
        for chapter in unittest.chapters:
            yield Enter(chapter)
            chapter_report = Report(chapter, unittest_report)
            for section in chapter.sections:
                yield Enter(section)
                section_report = Report(section, chapter_report)
                q_and_a = []
                for category in section.categories:
                    category.build()
                    q_and_a.extend(category.q_and_a)
                random.shuffle(q_and_a)
                for question in q_and_a:
                    yield Question(section_report, *question)
                yield Exit(section)
                section_report.finalize()
                yield section_report
            yield Exit(chapter)
            chapter_report.finalize()
            yield chapter_report
        yield Exit(self.test)
        unittest_report.finalize()
        yield unittest_report


class _Status(metaclass=abc.ABCMeta):
    """Abstract Base Class"""

    __slots__ = 'kind', 'name'

    @abc.abstractmethod
    def __init__(self, division):
        """Initialize the _Status instance with relevant event information."""
        self.kind = type(division).__name__
        self.name = division.name

    def __str__(self):
        """Convert the _Status into a string that can be displayed."""
        return f'{self.kind}: {self.name}'


class Enter(_Status):
    """Enter(division) -> Enter instance"""

    __slots__ = ()

    def __init__(self, division):
        """Make the Enter class instantiable."""
        super().__init__(division)


class Exit(_Status):
    """Exit(division) -> Exit instance"""

    __slots__ = ()

    def __init__(self, division):
        """Make the Exit class instantiable."""
        super().__init__(division)


class Report:
    """Report(level, parent=None) -> Report instance"""

    __slots__ = (
        '__level',
        '__parent',
        '__right',
        '__wrong',
        '__problems',
        '__finalized'
    )

    def __init__(self, level, parent=None):
        """Initialize the Report instance so that it can track progress."""
        self.__level = type(level).__name__
        self.__parent = parent
        self.__right = 0
        self.__wrong = 0
        self.__problems = []
        self.__finalized = False

    def right_answer(self):
        """Report that a question has been answered correctly."""
        if self.__finalized:
            raise RuntimeError('Report is finalized!')
        self.__right += 1

    def wrong_answer(self):
        """Report that a question has been answered incorrectly."""
        if self.__finalized:
            raise RuntimeError('Report is finalized!')
        self.__wrong += 1

    def review(self, question, answer):
        """Record a question and answer that will need to be reviewed."""
        if self.__finalized:
            raise RuntimeError('Report is finalized!')
        self.__problems.append((question, answer))

    def get_problems(self):
        """Yield back answers that teach students what they got wrong."""
        if not self.__finalized:
            raise RuntimeError('Report is not finalized!')
        for question, answer in self.__problems:
            yield Answer(answer, *question)

    def finalize(self):
        """Finish the report and send results to any report higher up."""
        if self.__finalized:
            raise RuntimeError('Report is finalized!')
        self.__finalized, parent = True, self.__parent
        if parent is not None:
            parent.__right += self.__right
            parent.__wrong += self.__wrong
            parent.__problems.extend(self.__problems)

    @property
    def level(self):
        """Read-only level property (level in the testbank structure)."""
        return self.__level

    @property
    def right(self):
        """Read-only right property (how many answers were correct)."""
        if not self.__finalized:
            raise RuntimeError('Report is not finalized!')
        return self.__right

    @property
    def wrong(self):
        """Read-only wrong property (how many answers were incorrect)."""
        if not self.__finalized:
            raise RuntimeError('Report is not finalized!')
        return self.__wrong

    @property
    def total(self):
        """Read-only total property (how many answers have been given)."""
        if not self.__finalized:
            raise RuntimeError('Report is not finalized!')
        return self.__right + self.__wrong

    @property
    def final(self):
        """Read-only final property (flag stating if report is top-level)."""
        return self.__parent is None


class Question:
    """Question(
        report, category, question, choices, right
    ) -> Question instance"""

    __slots__ = (
        '__report',
        '__category',
        '__question',
        '__choices',
        '__right',
        '__answered',
        '__q_and_a'
    )

    def __init__(self, report, category, question, choices, right):
        """Initialize the Question instance with all that it needs to know."""
        self.__report = report
        self.__category = category
        self.__question = question
        self.__choices = choices
        self.__right = right
        self.__answered = False
        self.__q_and_a = quizcore.Record(category, question, choices, right)

    @property
    def category(self):
        """Read-only category property (type of question)."""
        return self.__category

    @property
    def question(self):
        """Read-only question property (text for the question)."""
        return self.__question

    @property
    def choices(self):
        """Read-only choices property (array of possible answers)."""
        return self.__choices

    def answer(self, index_or_string):
        """Allows caller to answer the question via int or str object."""
        if self.__answered:
            raise RuntimeError('Question has already been answered!')
        if isinstance(index_or_string, int):
            index_or_string = self.__choices[index_or_string]
        if index_or_string == self.__right:
            self.__report.right_answer()
        else:
            self.__report.wrong_answer()
            self.__report.review(self.__q_and_a, index_or_string)
        self.__answered = True

    @property
    def _right_answer(self):
        """Read-only _right_answer property (private)."""
        return self.__right


class Answer(Question):
    """Answer(answer, category, question, choices, right) -> Answer instance"""

    __slots__ = '__answer'

    def __init__(self, answer, category, question, choices, right):
        """Initialize the Answer instance like it was a Question."""
        super().__init__(None, category, question, choices, right)
        self.__answer = answer

    # noinspection PyMethodOverriding
    @property
    def answer(self):
        """Read-only answer property (has the answer that was given)."""
        return self.__answer

    @property
    def right(self):
        """Read-only right property (says what the correct answer is)."""
        return self._right_answer
