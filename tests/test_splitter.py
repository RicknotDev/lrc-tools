"""Tests for splitter.py — phrase splitting logic."""

from __future__ import annotations

import unittest

from lrc_tools.splitter import split_phrase_intelligently, find_split_point, find_all_split_points


class TestFindSplitPoints(unittest.TestCase):
    def test_find_all_split_points_commas(self):
        words = "a b, c d".split()
        points = find_all_split_points(" ".join(words))
        self.assertIn(2, points)  # after "b,"

    def test_find_all_split_points_period(self):
        words = "a b. c d".split()
        points = find_all_split_points(" ".join(words))
        self.assertIn(2, points)

    def test_no_split_points(self):
        words = "a b c d".split()
        points = find_all_split_points(" ".join(words))
        self.assertEqual(points, [])


class TestFindSplitPoint(unittest.TestCase):
    def test_find_at_punctuation(self):
        words = "hello world. foo bar".split()
        idx = find_split_point(words, 2)
        self.assertEqual(idx, 2)  # after "world."

    def test_find_at_conjunction(self):
        words = "a b c and d e f".split()
        idx = find_split_point(words, 3)
        self.assertEqual(idx, 3)  # at "and"

    def test_fallback_to_prefer_index(self):
        words = "a b c d e f".split()
        idx = find_split_point(words, 3)
        self.assertEqual(idx, 3)


class TestSplitPhraseIntelligently(unittest.TestCase):
    def test_short_phrase_no_split(self):
        result = split_phrase_intelligently("Hello world", 2.0, 0.0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], 'Hello world')
        self.assertEqual(result[0]['timestamp'], 0.0)

    def test_split_on_commas(self):
        text = "Hello, world, foo bar"
        result = split_phrase_intelligently(text, 6.0, 0.0, split_on_commas=True)
        self.assertGreaterEqual(len(result), 2)
        for entry in result:
            self.assertNotIn(',', entry['text'])

    def test_long_phrase_splits_by_duration(self):
        text = "a b c d e f g h i j k l m n o p"
        words = text.split()
        duration = 10.0
        result = split_phrase_intelligently(text, duration, 0.0, max_phrase_duration=2.5, max_words_per_phrase=8)
        self.assertGreater(len(result), 1)
        total_words = sum(len(r['text'].split()) for r in result)
        self.assertEqual(total_words, len(words))

    def test_no_commas_short_phrase(self):
        result = split_phrase_intelligently("Hello world", 1.5, 0.0, max_phrase_duration=2.0)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], 'Hello world')

    def test_timestamps_increase(self):
        text = "Hello world foo bar baz qux"
        result = split_phrase_intelligently(text, 4.0, 0.0, max_phrase_duration=2.0)
        for i in range(1, len(result)):
            self.assertGreaterEqual(result[i]['timestamp'], result[i - 1]['timestamp'])


if __name__ == "__main__":
    unittest.main()
