"""Shared utility functions for lrc-tools."""


def count_syllables(word: str) -> int:
    word = word.lower().strip(".,!?;:'\"")
    if not word:
        return 1
    if word.endswith("e"):
        word = word[:-1]
    vowels = "aeiouy"
    syllable_count = 0
    previous_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            syllable_count += 1
        previous_was_vowel = is_vowel
    if word.endswith("le") and len(word) > 2 and word[-3] not in vowels:
        syllable_count += 1
    return max(1, syllable_count)
