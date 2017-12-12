#! /usr/bin/env python3
"""XML document parser for building a simple node-based DOM.

Ensuring that test XML documents are parsed correctly and follow certain rules
for validation purposes is the whole reason this module exists. Users of this
module only have to import it and call the parse function with the filename of
the document they want to process. The root of the DOM is returned."""

__author__ = 'Stephen "Zero" Chappell ' \
             '<stephen.paul.chappell@atlantis-zero.net>'
__date__ = '11 December 2017'
__version__ = 2, 6, 1
__all__ = [
    'BankParser',
    'TestBank',
    'Chapter',
    'Section',
    'Category',
    'Fact',
    'Question',
    'Answer'
]

import abc
import xml.sax
import xml.sax.handler


class BankParser(xml.sax.handler.ContentHandler):
    """BankParser() -> BankParser instance"""

    @classmethod
    def parse(cls, filename):
        """Parse the XML specified by filename and return the root node."""
        parser = cls()
        xml.sax.parse(filename, parser)
        return parser.root_node

    def __init__(self):
        """Initialize the BankParser instance with an element context list."""
        super().__init__()
        self.context = []
        self.root_node = None

    def startElement(self, name, attributes):
        """Record when elements are introduced in the XML document."""
        if name == 'testbank':
            # Validate
            if self.context:
                raise RuntimeError('Context should be empty!')
            # Specific
            self.context.append(TestBank(attributes.getValue('name')))
        elif name == 'chapter':
            # Validate
            if not isinstance(self.context[-1], TestBank):
                raise RuntimeError('Chapter should be in context of testbank!')
            # Specific
            self.context.append(Chapter(attributes.getValue('name')))
        elif name == 'section':
            # Validate
            if not isinstance(self.context[-1], Chapter):
                raise RuntimeError('Section should be in context of chapter!')
            # Specific
            self.context.append(Section(attributes.getValue('name')))
        elif name == 'category':
            # Validate
            if not isinstance(self.context[-1], Section):
                raise RuntimeError('Category should be in context of section!')
            # Specific
            self.context.append(Category(attributes.getValue('type')))
        elif name == 'fact':
            # Validate
            if not isinstance(self.context[-1], Category):
                raise RuntimeError('Fact should be in context of category!')
            # Specific
            self.context.append(Fact(
                attributes.getValue('type')
                if self.context[-1].attr == 'multiple_choice' else
                None
            ))
        elif name == 'question':
            # Validate
            if not isinstance(self.context[-1], Fact):
                raise RuntimeError('Question should be in context of fact!')
            # Specific
            self.context.append(Question())
        elif name == 'answer':
            # Validate
            if not isinstance(self.context[-1], Fact):
                raise RuntimeError('Answer should be in context of fact!')
            # Specific
            self.context.append(Answer())
        else:
            # Something is wrong with this document.
            raise ValueError(name)

    def characters(self, content):
        """Add character data to the node at the top of the context."""
        self.context[-1].add_text(content)

    def endElement(self, name):
        """Record an element's end and update the document's node tree."""
        node = self.context.pop()
        if name == 'testbank':
            self.root_node = node
        else:
            self.context[-1].add_child(node)


class _Node(metaclass=abc.ABCMeta):
    """Abstract Base Class"""

    __slots__ = 'attr', 'text', 'children'

    ATTR_NAME = None

    @abc.abstractmethod
    def __init__(self, attr):
        """Initialize the _Node instance with whatever attribute it has."""
        self.attr = attr
        self.text = ''
        self.children = []

    def __repr__(self):
        """Build a XML representation of the node with its children."""
        name = type(self).__name__.lower()
        attr = '' if self.attr is None else f' {self.ATTR_NAME}="{self.attr}"'
        cache = [f'<{name}{attr}>']
        for child in self.children:
            lines = repr(child).split('\n')
            lines = map(lambda line: '    ' + line, lines)
            cache.append('\n' + '\n'.join(lines))
        cache.append(self.text if self.ATTR_NAME is None else '\n')
        cache.append(f'</{name}>')
        return ''.join(cache)

    def add_text(self, content):
        """Add character data to the node's text content."""
        self.text += content

    def add_child(self, node):
        """Add a child to this node's list of children."""
        self.children.append(node)


class TestBank(_Node):
    """TestBank(attr) -> TestBank instance"""

    __slots__ = ()

    ATTR_NAME = 'name'

    def __init__(self, attr):
        """Allow this node type to be instantiated."""
        super().__init__(attr)


class Chapter(_Node):
    """Chapter(attr) -> Chapter instance"""

    __slots__ = ()

    ATTR_NAME = 'name'

    def __init__(self, attr):
        """Allow this node type to be instantiated."""
        super().__init__(attr)


class Section(_Node):
    """Section(attr) -> Section instance"""

    __slots__ = ()

    ATTR_NAME = 'name'

    def __init__(self, attr):
        """Allow this node type to be instantiated."""
        super().__init__(attr)


class Category(_Node):
    """Category(attr) -> Category instance"""

    __slots__ = ()

    ATTR_NAME = 'type'

    def __init__(self, attr):
        """Allow this node type to be instantiated and validate."""
        if attr not in {'matching', 'multiple_choice', 'true_or_false'}:
            raise RuntimeError('Type of category not recognized!')
        super().__init__(attr)


class Fact(_Node):
    """Fact(attr) -> Fact instance"""

    __slots__ = ()

    ATTR_NAME = 'type'

    def __init__(self, attr):
        """Allow this node type to be instantiated."""
        super().__init__(attr)


class Question(_Node):
    """Question() -> Question instance"""

    __slots__ = ()

    def __init__(self):
        """Allow this node type to be instantiated."""
        super().__init__(None)


class Answer(_Node):
    """Answer() -> Answer instance"""

    __slots__ = ()

    def __init__(self):
        """Allow this node type to be instantiated."""
        super().__init__(None)
