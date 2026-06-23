"""Tests for utils.py — count_syllables."""

from __future__ import annotations

import unittest

from lrc_tools.utils import count_syllables


class TestCountSyllables(unittest.TestCase):
    def test_single_syllable(self):
        self.assertEqual(count_syllables("a"), 1)
        self.assertEqual(count_syllables("I"), 1)
        self.assertEqual(count_syllables("the"), 1)

    def test_two_syllables(self):
        self.assertEqual(count_syllables("hello"), 2)
        self.assertEqual(count_syllables("water"), 2)

    def test_three_syllables(self):
        self.assertEqual(count_syllables("elephant"), 3)

    def test_silent_e(self):
        self.assertEqual(count_syllables("love"), 1)
        self.assertEqual(count_syllables("make"), 1)

    def test_y_as_vowel(self):
        self.assertEqual(count_syllables("happy"), 2)

    def test_empty_string(self):
        self.assertEqual(count_syllables(""), 1)

    def test_punctuation_stripped(self):
        self.assertEqual(count_syllables("hello!"), 2)
        self.assertEqual(count_syllables("world."), 1)

    def test_apostrophe(self):
        self.assertEqual(count_syllables("don't"), 1)

    def test_minimum_one(self):
        self.assertEqual(count_syllables("x"), 1)


if __name__ == "__main__":
    unittest.main()
