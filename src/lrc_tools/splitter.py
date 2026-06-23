"""Phrase splitting logic for LRC processor."""

from typing import List, Dict



def find_all_split_points(text: str) -> List[int]:
    words = text.split()
    split_points = []
    for i, word in enumerate(words):
        if any(word.rstrip().endswith(p) for p in [',', '.', '!', '?', ';', '\u2014', '-']):
            if i + 1 < len(words):
                split_points.append(i + 1)
    return split_points


def find_split_point(words: List[str], prefer_index: int) -> int:
    punctuation_priority = [
        ['.', '!', '?'],
        [',', ';', '\u2014', '-'],
        ['and', 'but', 'or', 'so', 'then', 'when', 'while', 'if']
    ]

    search_radius = min(3, len(words) // 3)

    for punct_list in punctuation_priority:
        for offset in range(search_radius + 1):
            for direction in [0, 1, -1]:
                if direction == 0:
                    idx = prefer_index
                elif direction == 1:
                    idx = prefer_index + offset
                else:
                    idx = prefer_index - offset

                if idx <= 0 or idx >= len(words):
                    continue

                prev_word = words[idx - 1]
                if any(prev_word.rstrip().endswith(p) for p in punct_list if not p.isalpha()):
                    return idx

                if words[idx].lower() in punct_list:
                    return idx

    return prefer_index


def split_phrase_intelligently(
    text: str,
    duration: float,
    start_time: float,
    max_phrase_duration: float = 2.5,
    max_words_per_phrase: int = 8,
    split_on_commas: bool = True
) -> List[Dict]:
    words = text.split()

    comma_splits = []
    for i, word in enumerate(words):
        if ',' in word:
            comma_splits.append(i + 1)

    if comma_splits and split_on_commas:
        result = []
        word_idx = 0

        for split_idx in comma_splits + [len(words)]:
            if split_idx <= word_idx:
                continue

            chunk_words = words[word_idx:split_idx]
            if not chunk_words:
                continue

            chunk_text = ' '.join(chunk_words)
            chunk_text = chunk_text.replace(',', '').strip()

            chunk_duration = (len(chunk_words) / len(words)) * duration

            result.append({
                'timestamp': start_time,
                'text': chunk_text
            })

            start_time += chunk_duration
            word_idx = split_idx

        return result

    if duration <= max_phrase_duration and len(words) <= max_words_per_phrase:
        return [{
            'timestamp': start_time,
            'text': text
        }]

    num_chunks = max(2, int(duration / max_phrase_duration) + 1)
    chunk_size = len(words) / num_chunks

    result = []
    current_start = start_time
    word_idx = 0

    for chunk_num in range(num_chunks):
        if chunk_num == num_chunks - 1:
            chunk_words = words[word_idx:]
        else:
            target_idx = word_idx + int(chunk_size)
            split_idx = find_split_point(words, target_idx)
            chunk_words = words[word_idx:split_idx]
            word_idx = split_idx

        if not chunk_words:
            continue

        chunk_text = ' '.join(chunk_words)

        chunk_duration = (len(chunk_words) / len(words)) * duration

        result.append({
            'timestamp': current_start,
            'text': chunk_text
        })

        current_start += chunk_duration

    return result
