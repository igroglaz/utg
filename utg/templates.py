# coding: utf-8

import re

from utg import logic
from utg import exceptions
from utg import words
from utg import relations as r

_VARIABLE_REGEX = re.compile(u'\[[^\]]+\]', re.UNICODE)

_VERBOSE_TO_PROPERTIES = logic.get_verbose_to_relations()

# "«[initiator|загл] [обратился|initiator|прш] ко мне с просьбой проследить за одним из жителей [receiver_position|рд]. Есть подозрения, что [receiver] проворачивает нечистые делишки.»"


class Substitution(object):
    __slots__ = ('id', 'dependencies')

    def __init__(self):
        self.id = None
        self.dependencies = []

    @classmethod
    def parse(cls, variable, externals):
        slugs = variable[1:-1].lower().split('|')

        if not slugs[0]:
            raise exceptions.WrongDependencyFormatError(dependency=variable)

        s = cls()

        s.id = slugs[0].strip()

        for slug in slugs[1:]:
            slug = slug.strip()
            if slug in externals:
                s.dependencies.append(slug)
            else:
                s.dependencies.append(cls.parse_properties(slug))

        return s


    @classmethod
    def parse_properties(cls, text):
        properties = words.Properties()
        for slug in text.split(','):
            slug.strip()

            if not slug:
                continue

            if slug not in _VERBOSE_TO_PROPERTIES:
                raise exceptions.UnknownVerboseIdError(verbose_id=slug)

            properties.update(_VERBOSE_TO_PROPERTIES[slug])

        return properties


    def _merge_properties(self, externals):
        properties = words.Properties()

        for dependency in self.dependencies:
            if isinstance(dependency, words.Properties):
                properties.update(dependency)
                continue

            if dependency not in externals:
                raise exceptions.ExternalDependecyNotFoundError(dependency=dependency)

            properties.update(externals[dependency].properties)

        return properties


    def get_word(self, externals, dictionary):
        properties = self._merge_properties(externals=externals)

        if self.id in externals:
            word = externals[self.id]
        else:
            word = dictionary.get_word(self.id, type=properties.get(r.WORD_TYPE))

        return word.form(properties)


class Template(object):
    __slots__ = ('_substitutions', '_template')

    def __init__(self):
        self._substitutions = []
        self._template = None

    def parse(self, text, dictionary):

        variables = _VARIABLE_REGEX.findall(text)

        for i, variable in enumerate(variables):
            self._substitutions.append(Substitution.parse(variable))
            text = text.replace(variable, '%s', max=1)

        self._template = text

    def substitute(self, externals, dictionary):
        substitutions = [substitution.get_word(dictionary, externals) for substitution in self._substitutions]
        return self._template % substitutions
