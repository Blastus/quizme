#! /usr/bin/env python3
"""Support for organizing question and answer data into a useful form.

The classes here echo a similar structure to the testbank module, but while
those other classes provide a simple DOM, these classes validate and structure
the data into a usable form. Questions and answers are automatically organized
so that choices are available and sensible for the question being asked."""

__author__ = 'Stephen "Zero" Chappell ' \
             '<stephen.paul.chappell@atlantis-zero.net>'
__date__ = '11 December 2017'
__version__ = 2, 6, 1
__all__ = [
    'UnitTest',
    'Chapter',
    'Section',
    'Record',
    'Matching',
    'MultipleChoice',
    'TrueOrFalse',
    'Fact',
    'Question',
    'Answer'
]

import abc
import collections
import random

from . import testbank


class UnitTest:
    """UnitTest(root_node) -> UnitTest instance"""

    __slots__ = 'name', 'chapters'

    def __init__(self, root_node):
        """Initialize the UnitTest instance and validate its data."""
        self.name = root_node.attr
        self.chapters = list(map(Chapter, root_node.children))
        if not self.chapters:
            raise RuntimeError('UnitTest is empty!')


class Chapter:
    """Chapter(chapter) -> Chapter instance"""

    __slots__ = 'name', 'sections'

    def __init__(self, chapter):
        """Initialize the Chapter instance and validate its data."""
        self.name = chapter.attr
        self.sections = list(map(Section, chapter.children))
        if not self.sections:
            raise RuntimeError('Chapter is empty!')


class Section:
    """Section(section) -> Section instance"""

    __slots__ = 'name', 'categories'

    def __init__(self, section):
        """Initialize the Section instance and validate its data."""
        self.name = section.attr
        self.categories = list(map(self.get_category, section.children))
        if not self.categories:
            raise RuntimeError('Section is empty!')

    @staticmethod
    def get_category(category):
        """Find the correct category class and return it."""
        try:
            return _CATEGORY[category.attr](category)
        except KeyError:
            raise ValueError(category.attr)


# Create a class that has everything needed to be known to handle questions.
Record = collections.namedtuple('Record', 'kind, question, choices, answer')


class _Category(metaclass=abc.ABCMeta):
    """Abstract Base Class"""

    __slots__ = 'facts', 'q_and_a'

    CHOICES = 0
    NAME = ''

    @abc.abstractmethod
    def __init__(self, category):
        """Initialize the Facts for the question category and validate."""
        self.facts = [Fact(child, isinstance(self, TrueOrFalse))
                      for child in category.children]
        if not self.facts:
            raise RuntimeError('Category is empty!')
        self.q_and_a = []

    @abc.abstractmethod
    def build(self):
        """Construct the table of questions and answers."""
        pass


class _MCM(_Category):
    """Abstract Base Class"""

    __slots__ = ()

    @abc.abstractmethod
    def __init__(self, category):
        """Keep this class abstract so that it cannot be constructed."""
        super().__init__(category)

    def build(self):
        """Construct the table of questions and answers."""
        kinds = {}
        for fact in self.facts:
            fact.build()
            for question in fact.q_to_a:
                kinds.setdefault(fact.kind, {'question': {}, 'answer': {}})[
                    'question'].setdefault(question, set()).update(
                    fact.q_to_a[question])
            for answer in fact.a_to_q:
                kinds.setdefault(fact.kind, {'question': {}, 'answer': {}})[
                    'answer'].setdefault(answer, set()).update(
                    fact.a_to_q[answer])
        for kind in kinds:
            questions = set(kinds[kind]['question'])
            answers = set(kinds[kind]['answer'])
            for question in questions:
                wrong = answers.difference(kinds[kind]['question'][question])
                sample = random.sample(wrong, min(len(wrong), self.CHOICES))
                right = random.choice(tuple(kinds[kind]['question'][question]))
                sample.append(right)
                random.shuffle(sample)
                self.q_and_a.append(Record(
                    self.NAME, question, tuple(sample), right
                ))


class Matching(_MCM):
    """Matching(category) -> Matching instance"""

    __slots__ = ()

    CHOICES = 25
    NAME = 'Matching'

    def __init__(self, category):
        """Initialize the Matching instance with data from a category."""
        super().__init__(category)


class MultipleChoice(_MCM):
    """MultipleChoice(category) -> MultipleChoice instance"""

    __slots__ = ()

    CHOICES = 3
    NAME = 'Multiple Choice'

    def __init__(self, category):
        """Initialize the MultipleChoice instance with data from a category."""
        super().__init__(category)


class TrueOrFalse(_Category):
    """TrueOrFalse(category) -> TrueOrFalse instance"""

    __slots__ = ()

    def __init__(self, category):
        """Initialize the TrueOrFalse instance with data from a category."""
        super().__init__(category)

    def build(self):
        """Construct the table of questions and answers."""
        questions = {}
        for fact in self.facts:
            fact.build()
            for question in fact.q_to_a:
                questions.setdefault(question, set()).update(
                    fact.q_to_a[question]
                )
        for question in questions:
            if len(questions[question]) != 1:
                raise RuntimeError('Question is invalid!')
            sample = random.sample(('True', 'False'), 2)
            right = tuple(questions[question])[0]
            self.q_and_a.append(Record(
                'True or False', question, tuple(sample), right
            ))


_CATEGORY = dict(
    matching=Matching,
    multiple_choice=MultipleChoice,
    true_or_false=TrueOrFalse
)


class Fact:
    """Fact(fact, true_or_false) -> Fact instance"""

    __slots__ = 'kind', 'questions', 'answers', 'q_to_a', 'a_to_q'

    def __init__(self, fact, true_or_false):
        """Initialize the Fact instance and sort the questions and answers."""
        self.kind = fact.attr
        self.questions = []
        self.answers = []
        for child in fact.children:
            if isinstance(child, testbank.Question):
                self.questions.append(Question(child))
            elif isinstance(child, testbank.Answer):
                self.answers.append(Answer(child, true_or_false))
            else:
                raise TypeError(child)
        if not self.answers:
            raise RuntimeError('Fact is empty!')
        self.q_to_a = {}
        self.a_to_q = {}

    def build(self):
        """Construct the mappings for questions and answers."""
        questions = frozenset(question.text for question in self.questions)
        answers = frozenset(answer.text for answer in self.answers)
        self.q_to_a.update((question, answers) for question in questions)
        self.a_to_q.update((answer, questions) for answer in answers)


class Question:
    """Question(question) -> Question instance"""

    __slots__ = 'text'

    def __init__(self, question):
        """Initialize the Question instance with the question's text."""
        self.text = question.text


class Answer:
    """Answer(answer, true_or_false) -> Answer instance"""

    __slots__ = 'text'

    def __init__(self, answer, true_or_false):
        """Initialize the Answer instance and validate if needed."""
        if true_or_false and answer.text not in {'True', 'False'}:
            raise RuntimeError('Answer is invalid!')
        self.text = answer.text
