from __future__ import annotations

import re
import unicodedata
from typing import Any

from config import FILLER_WORDS, STOPWORDS
from modules.utils import count_words

TOKEN_PATTERN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ']{2,}", flags=re.UNICODE)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")
FILLER_PATTERN = re.compile(
    r"\b(?:" + "|".join(sorted((re.escape(word) for word in FILLER_WORDS), key=len, reverse=True)) + r")\b",
    flags=re.IGNORECASE,
)


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def clean_text(text: str) -> str:
    normalized = normalize_unicode(text)
    normalized = normalized.replace("\r", "\n")
    normalized = FILLER_PATTERN.sub(" ", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{2,}", "\n", normalized)
    normalized = re.sub(r"\s+([,;:.!?])", r"\1", normalized)
    normalized = re.sub(r"([,;:.!?]){2,}", r"\1", normalized)
    normalized = re.sub(r"\s{2,}", " ", normalized)
    return normalized.strip()


def split_sentences(text: str) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_PATTERN.split(cleaned) if sentence.strip()]
    return sentences


def tokenize(text: str, lowercase: bool = True) -> list[str]:
    normalized = normalize_unicode(text)
    tokens = TOKEN_PATTERN.findall(normalized)
    if lowercase:
        return [token.lower() for token in tokens]
    return tokens


def filter_stopwords(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in STOPWORDS and len(token) > 2]


def build_analysis_corpus(text: str) -> dict[str, Any]:
    cleaned_text = clean_text(text)
    sentences = split_sentences(cleaned_text)
    tokens = tokenize(cleaned_text, lowercase=True)
    filtered_tokens = filter_stopwords(tokens)
    sentence_lengths = [count_words(sentence) for sentence in sentences]
    lexical_diversity = round(len(set(filtered_tokens)) / max(1, len(filtered_tokens)), 3)

    return {
        "cleaned_text": cleaned_text,
        "sentences": sentences,
        "tokens": tokens,
        "filtered_tokens": filtered_tokens,
        "token_count": len(tokens),
        "filtered_token_count": len(filtered_tokens),
        "sentence_count": len(sentences),
        "sentence_lengths": sentence_lengths,
        "lexical_diversity": lexical_diversity,
    }
