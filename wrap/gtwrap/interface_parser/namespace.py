"""
GTSAM Copyright 2010-2020, Georgia Tech Research Corporation,
Atlanta, Georgia 30332-0415
All Rights Reserved

See LICENSE for the license information

Classes and rules to parse a namespace.

Author: Duy Nguyen Ta, Fan Jiang, Matthew Sklar, Varun Agrawal, and Frank Dellaert
"""

# pylint: disable=unnecessary-lambda, expression-not-assigned

from typing import List, Union

from pyparsing import Forward, ParseResults, ZeroOrMore  # type: ignore

from .classes import Class, collect_namespaces
from .declaration import ForwardDeclaration, Include
from .enum import Enum
from .function import GlobalFunction
from .template import TypedefTemplateInstantiation
from .tokens import IDENT, LBRACE, NAMESPACE, RBRACE
from .type import Typename
from .variable import Variable


def find_sub_namespace(namespace: "Namespace",
                       str_namespaces: List["Namespace"]) -> list:
    """
    Get the namespaces nested under `namespace`, filtered by a list of namespace strings.

    Args:
        namespace: The top-level namespace under which to find sub-namespaces.
        str_namespaces: The list of namespace strings to filter against.
    """
    if not str_namespaces:
        return [namespace]

    sub_namespaces = (ns for ns in namespace.content
                      if isinstance(ns, Namespace))

    found_namespaces = [
        ns for ns in sub_namespaces if ns.name == str_namespaces[0]
    ]
    if not found_namespaces:
        return []

    res = []
    for found_namespace in found_namespaces:
        if ns := find_sub_namespace(found_namespace, str_namespaces[1:]):
            res += ns
    return res


class Namespace:
    """Rule for parsing a namespace in the interface file."""

    rule = Forward()
    rule << (
        NAMESPACE  #
        + IDENT("name")  #
        + LBRACE  #
        + ZeroOrMore(  # BR
            ForwardDeclaration.rule  #
            ^ Include.rule  #
            ^ Class.rule  #
            ^ TypedefTemplateInstantiation.rule  #
            ^ GlobalFunction.rule  #
            ^ Enum.rule  #
            ^ Variable.rule  #
            ^ rule  #
        )("content")  # BR
        + RBRACE  #
    ).setParseAction(lambda t: Namespace.from_parse_result(t))

    def __init__(self, name: str, content: ZeroOrMore, parent=''):
        self.name = name
        self.content = content
        self.parent = parent
        for child in self.content:
            child.parent = self

    @staticmethod
    def from_parse_result(t: ParseResults):
        """Return the result of parsing."""
        content = t.content.asList() if t.content else []
        return Namespace(t.name, content)

    def find_class_or_function(
            self, typename: Typename) -> Union[Class, GlobalFunction, ForwardDeclaration]:
        """
        Find the Class or GlobalFunction object given its typename.
        We have to traverse the tree of namespaces.
        """
        found_namespaces = find_sub_namespace(self, typename.namespaces)
        res = []
        for namespace in found_namespaces:
            classes_and_funcs = (c for c in namespace.content
                                 if isinstance(c, (Class, GlobalFunction, ForwardDeclaration)))
            res += [c for c in classes_and_funcs if c.name == typename.name]
        if not res:
            raise ValueError(f"Cannot find class {typename.name} in module!")
        elif len(res) > 1:
            raise ValueError(f"Found more than one classes {typename.name} in module!")
        else:
            return res[0]

    def top_level(self) -> "Namespace":
        """Return the top level namespace."""
        if self.name == '' or self.parent == '':
            return self
        else:
            return self.parent.top_level()

    def __repr__(self) -> str:
        return f"Namespace: {self.name}\n\t{self.content}"

    def full_namespaces(self) -> List["Namespace"]:
        """Get the full namespace list."""
        ancestors = collect_namespaces(self)
        if self.name:
            ancestors.append(self.name)
        return ancestors
