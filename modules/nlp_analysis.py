from __future__ import annotations

from collections import Counter
from typing import Any

from config import (
    ACTION_SIGNAL_LEXICON,
    CATEGORY_KEYWORDS,
    CATEGORY_LABELS,
    COGNITIVE_SIGNAL_LEXICON,
    CONTRAST_CONNECTORS,
    DISCLAIMER_TEXT,
    IDEAS_LIMIT,
    KEYWORD_LIMIT,
    RECOMMENDATION_LIMIT,
    SALIENT_SENTENCE_LIMIT,
    SCORE_EXPLANATIONS,
    THEME_KEYWORDS,
    TOP_THEME_LIMIT,
    TENSION_LIMIT,
)
from modules.text_cleaning import build_analysis_corpus, tokenize
from modules.utils import clamp, dedupe_preserve_order, truncate_text

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
+except Exception:  # pragma: no cover - optional safety during local bootstrap
+    TfidfVectorizer = None
+
+
+def _match_terms(sentence: str, lexicon: set[str]) -> int:
+    lowered_sentence = sentence.lower()
+    sentence_tokens = set(tokenize(lowered_sentence))
+    score = 0
+    for term in lexicon:
+        lowered_term = term.lower()
+        if " " in lowered_term:
+            if lowered_term in lowered_sentence:
+                score += 2
+        elif lowered_term in sentence_tokens:
+            score += 1
+    return score
+
+
+def extract_keywords(cleaned_text: str, filtered_tokens: list[str]) -> list[dict[str, Any]]:
+    weighted_terms: dict[str, float] = {}
+    raw_counts = Counter(filtered_tokens)
+    for token, count in raw_counts.items():
+        weighted_terms[token] = float(count)
+
+    if cleaned_text and TfidfVectorizer is not None:
+        try:
+            vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=40)
+            matrix = vectorizer.fit_transform([cleaned_text])
+            features = vectorizer.get_feature_names_out()
+            scores = matrix.toarray()[0]
+            for term, score in sorted(zip(features, scores), key=lambda item: item[1], reverse=True):
+                if len(term) < 3:
+                    continue
+                weighted_terms[term] = weighted_terms.get(term, 0.0) + float(score * 20)
+        except ValueError:
+            pass
+
+    results: list[dict[str, Any]] = []
+    for term, weight in sorted(weighted_terms.items(), key=lambda item: item[1], reverse=True):
+        term_count = raw_counts.get(term, cleaned_text.lower().count(term)) or 1
+        if term_count <= 0:
+            continue
+        results.append({"term": term, "count": int(term_count), "weight": round(weight, 2)})
+        if len(results) >= KEYWORD_LIMIT:
+            break
+    return results
+
+
+def detect_themes(filtered_tokens: list[str], sentences: list[str]) -> tuple[list[dict[str, Any]], Counter]:
+    token_counter = Counter(filtered_tokens)
+    theme_counter: Counter = Counter()
+    lowered_sentences = [sentence.lower() for sentence in sentences]
+
+    for theme, lexicon in THEME_KEYWORDS.items():
+        for term in lexicon:
+            lowered_term = term.lower()
+            if " " in lowered_term:
+                theme_counter[theme] += sum(1 for sentence in lowered_sentences if lowered_term in sentence)
+            else:
+                theme_counter[theme] += token_counter.get(lowered_term, 0)
+
+    dominant_themes = [
+        {"theme": theme, "count": int(count)}
+        for theme, count in theme_counter.most_common(TOP_THEME_LIMIT)
+        if count > 0
+    ]
+    return dominant_themes, theme_counter
+
+
+def categorize_sentences(sentences: list[str]) -> tuple[dict[str, list[str]], Counter, list[dict[str, Any]]]:
+    category_sentences: dict[str, list[str]] = {key: [] for key in CATEGORY_LABELS}
+    category_counts: Counter = Counter()
+    sentence_records: list[dict[str, Any]] = []
+
+    for sentence in sentences:
+        hits: dict[str, int] = {}
+        for category, lexicon in CATEGORY_KEYWORDS.items():
+            score = _match_terms(sentence, lexicon)
+            if score > 0:
+                hits[category] = score
+                category_counts[category] += score
+                if sentence not in category_sentences[category] and len(category_sentences[category]) < 3:
+                    category_sentences[category].append(sentence)
+        sentence_records.append({"sentence": sentence, "hits": hits})
+    return category_sentences, category_counts, sentence_records
+
+
+def collect_signal_matches(sentences: list[str], lexicon_map: dict[str, set[str]], limit: int = 4) -> tuple[list[dict[str, Any]], Counter]:
+    collected: list[dict[str, Any]] = []
+    counts: Counter = Counter()
+    for signal, lexicon in lexicon_map.items():
+        evidence: list[str] = []
+        signal_count = 0
+        for sentence in sentences:
+            hits = _match_terms(sentence, lexicon)
+            if hits > 0:
+                signal_count += hits
+                if len(evidence) < 2:
+                    evidence.append(truncate_text(sentence, 170))
+        if signal_count > 0:
+            counts[signal] = signal_count
+            collected.append(
+                {
+                    "signal": signal,
+                    "count": signal_count,
+                    "level": "eleve" if signal_count >= 4 else "modere" if signal_count >= 2 else "leger",
+                    "evidence": evidence,
+                }
+            )
+    collected.sort(key=lambda item: item["count"], reverse=True)
+    return collected[:limit], counts
+
+
+def detect_contradictions(sentence_records: list[dict[str, Any]]) -> list[str]:
+    contradictions: list[str] = []
+    for record in sentence_records:
+        sentence = record["sentence"]
+        lowered = sentence.lower()
+        hits = record["hits"]
+        if any(connector in lowered for connector in CONTRAST_CONNECTORS):
+            contradictions.append(f"Tension explicite : {truncate_text(sentence, 170)}")
+            continue
+        if "vision" in hits and "blockages" in hits:
+            contradictions.append(f"Aspiration et frein coexistent dans la meme phrase : {truncate_text(sentence, 170)}")
+            continue
+        if "action" in hits and "emotion" in hits and "coherence" not in hits:
+            contradictions.append(f"Une volonte d'action semble cohabiter avec une charge emotionnelle encore vive : {truncate_text(sentence, 170)}")
+    return dedupe_preserve_order(contradictions)[:TENSION_LIMIT]
+
+
+def select_salient_sentences(
+    sentences: list[str],
+    sentence_records: list[dict[str, Any]],
+    keyword_frequencies: list[dict[str, Any]],
+) -> list[str]:
+    keyword_terms = [item["term"].lower() for item in keyword_frequencies[:8]]
+    scored_sentences: list[tuple[float, str]] = []
+
+    for record in sentence_records:
+        sentence = record["sentence"]
+        lowered = sentence.lower()
+        keyword_score = sum(1 for term in keyword_terms if term and term in lowered)
+        category_score = sum(record["hits"].values())
+        length_bonus = 2 if 8 <= len(sentence.split()) <= 35 else 0
+        scored_sentences.append((category_score * 3 + keyword_score * 2 + length_bonus, sentence))
+
+    scored_sentences.sort(key=lambda item: item[0], reverse=True)
+    selected = [sentence for _, sentence in scored_sentences if sentence.strip()]
+    if not selected:
+        selected = sentences[:SALIENT_SENTENCE_LIMIT]
+    return dedupe_preserve_order(selected)[:SALIENT_SENTENCE_LIMIT]
+
+
+def compute_scores(
+    corpus: dict[str, Any],
+    category_counts: Counter,
+    emotional_counts: Counter,
+    cognitive_counts: Counter,
+    action_counts: Counter,
+    theme_counter: Counter,
+    contradictions: list[str],
+) -> dict[str, int]:
+    lexical_diversity = corpus.get("lexical_diversity", 0.0)
+    theme_total = max(1, sum(theme_counter.values()))
+    theme_concentration = (max(theme_counter.values()) / theme_total) if theme_counter else 0.0
+    confusion_hits = emotional_counts.get("confusion", 0) + cognitive_counts.get("hesitation", 0) + cognitive_counts.get("rumination", 0)
+    clarity_hits = cognitive_counts.get("clarification", 0) + cognitive_counts.get("insight", 0) + category_counts.get("coherence", 0)
+    action_hits = sum(action_counts.values()) + category_counts.get("action", 0)
+    emotional_load_hits = (
+        emotional_counts.get("stress", 0)
+        + emotional_counts.get("frustration", 0)
+        + emotional_counts.get("doute", 0)
+        + emotional_counts.get("fatigue", 0)
+        + emotional_counts.get("motivation", 0)
+        + emotional_counts.get("enthousiasme", 0)
+    )
+
+    scores = {
+        "clarity": round(clamp(38 + clarity_hits * 7 + lexical_diversity * 18 + theme_concentration * 18 - confusion_hits * 6 - len(contradictions) * 5)),
+        "emotional_load": round(clamp(18 + emotional_load_hits * 8 + emotional_counts.get("stress", 0) * 3 + emotional_counts.get("frustration", 0) * 2)),
+        "action_orientation": round(clamp(22 + action_hits * 7 + category_counts.get("resources", 0) * 4 - emotional_counts.get("doute", 0) * 4)),
+        "mental_dispersion": round(clamp(16 + confusion_hits * 8 + len(theme_counter) * 3 + len(contradictions) * 6 - category_counts.get("coherence", 0) * 3)),
+        "internal_coherence": round(clamp(52 + theme_concentration * 22 + category_counts.get("coherence", 0) * 6 + cognitive_counts.get("clarification", 0) * 4 - len(contradictions) * 10 - confusion_hits * 4)),
+    }
+    return scores
+
+
+def build_major_ideas(
+    dominant_themes: list[dict[str, Any]],
+    category_sentences: dict[str, list[str]],
+    emotional_signals: list[dict[str, Any]],
+    scores: dict[str, int],
+) -> list[str]:
+    ideas: list[str] = []
+    if dominant_themes:
+        ideas.append(f"Le theme le plus present concerne {dominant_themes[0]['theme'].lower()}.")
+    if category_sentences.get("vision"):
+        ideas.append("Une aspiration explicite ressort et donne une direction assez lisible au discours.")
+    if category_sentences.get("blockages"):
+        ideas.append("Des freins ou tensions recurrentes structurent encore une partie importante de la parole.")
+    if scores.get("action_orientation", 0) >= 55:
+        ideas.append("Le passage a l'action commence a prendre forme a travers des formulations concretes.")
+    else:
+        ideas.append("L'intention est presente, mais les prochaines etapes restent encore a solidifier.")
+    if emotional_signals:
+        top_signals = ", ".join(signal["signal"] for signal in emotional_signals[:2])
+        ideas.append(f"Le ton general laisse percevoir des signaux possibles de {top_signals}.")
+    return dedupe_preserve_order(ideas)[:IDEAS_LIMIT]
+
+
+def build_recommendations(
+    scores: dict[str, int],
+    contradictions: list[str],
+    category_sentences: dict[str, list[str]],
+    emotional_signals: list[dict[str, Any]],
+) -> list[str]:
+    recommendations: list[str] = []
+    if contradictions:
+        recommendations.append("Nommer clairement la tension principale en une phrase courte pour mieux arbitrer la suite.")
+    if scores.get("action_orientation", 0) < 55:
+        recommendations.append("Transformer un sujet recurrent en prochaine etape observable a court terme.")
+    else:
+        recommendations.append("Conserver l'elan d'action en precisant qui fait quoi, quand, et avec quel niveau d'engagement.")
+    if scores.get("emotional_load", 0) >= 60 or emotional_signals:
+        recommendations.append("Distinguer ce qui releve de la pression immediate et ce qui releve d'un choix plus structurel.")
+    if category_sentences.get("needs"):
+        recommendations.append("Formuler explicitement le besoin concret derriere le sujet pour clarifier les conditions de progression.")
+    if category_sentences.get("resources"):
+        recommendations.append("S'appuyer sur les ressources deja citees plutot que de repartir d'une page blanche.")
+    recommendations.append("Reprendre les phrases les plus marquantes pour en faire une ligne directrice de la prochaine session.")
+    return dedupe_preserve_order(recommendations)[:RECOMMENDATION_LIMIT]
+
+
+def build_summary(
+    dominant_themes: list[dict[str, Any]],
+    emotional_signals: list[dict[str, Any]],
+    scores: dict[str, int],
+    contradictions: list[str],
+) -> str:
+    theme_text = ", ".join(item["theme"].lower() for item in dominant_themes[:2]) or "clarification personnelle"
+    emotion_text = ", ".join(signal["signal"] for signal in emotional_signals[:2])
+
+    parts = [f"La session se concentre principalement sur {theme_text}."]
+    if emotion_text:
+        parts.append(f"Des signaux possibles de {emotion_text} traversent le discours.")
+    if scores.get("action_orientation", 0) >= 55:
+        parts.append("La parole contient deja plusieurs marqueurs de passage a l'action.")
+    else:
+        parts.append("Le passage a l'action reste present mais encore a structurer plus concretement.")
+    if contradictions:
+        parts.append("Une ou plusieurs tensions apparaissent entre aspiration, charge emotionnelle et execution.")
+    return " ".join(parts)
+
+
+def build_key_topics(dominant_themes: list[dict[str, Any]], keyword_frequencies: list[dict[str, Any]]) -> list[dict[str, Any]]:
+    key_topics: list[dict[str, Any]] = []
+    for theme in dominant_themes[:4]:
+        related_keywords = [item["term"] for item in keyword_frequencies if item["term"] in theme["theme"].lower()]
+        key_topics.append({
+            "topic": theme["theme"],
+            "strength": theme["count"],
+            "keywords": related_keywords[:3],
+        })
+    if not key_topics:
+        key_topics = [
+            {"topic": item["term"], "strength": item["count"], "keywords": [item["term"]]}
+            for item in keyword_frequencies[:4]
+        ]
+    return key_topics
+
+
+def analyze_transcript(text: str) -> dict[str, Any]:
+    corpus = build_analysis_corpus(text)
+    sentences = corpus["sentences"]
+    filtered_tokens = corpus["filtered_tokens"]
+    cleaned_text = corpus["cleaned_text"]
+
+    keyword_frequencies = extract_keywords(cleaned_text, filtered_tokens)
+    dominant_themes, theme_counter = detect_themes(filtered_tokens, sentences)
+    category_sentences, category_counts, sentence_records = categorize_sentences(sentences)
+    emotional_signals, emotional_counts = collect_signal_matches(sentences, EMOTIONAL_SIGNAL_LEXICON)
+    cognitive_signals, cognitive_counts = collect_signal_matches(sentences, COGNITIVE_SIGNAL_LEXICON)
+    action_signals, action_counts = collect_signal_matches(sentences, ACTION_SIGNAL_LEXICON)
+    contradictions = detect_contradictions(sentence_records)
+    salient_sentences = select_salient_sentences(sentences, sentence_records, keyword_frequencies)
+    scores = compute_scores(corpus, category_counts, emotional_counts, cognitive_counts, action_counts, theme_counter, contradictions)
+    major_ideas = build_major_ideas(dominant_themes, category_sentences, emotional_signals, scores)
+    recommendations = build_recommendations(scores, contradictions, category_sentences, emotional_signals)
+    summary = build_summary(dominant_themes, emotional_signals, scores, contradictions)
+    key_topics = build_key_topics(dominant_themes, keyword_frequencies)
+
+    structured_categories = {
+        CATEGORY_LABELS[key]: category_sentences.get(key, [])
+        for key in CATEGORY_LABELS
+        if category_sentences.get(key)
+    }
+
+    return {
+        "summary": summary,
+        "major_ideas": major_ideas,
+        "key_topics": key_topics,
+        "dominant_themes": dominant_themes,
+        "emotional_signals": emotional_signals,
+        "cognitive_signals": cognitive_signals,
+        "action_signals": action_signals,
+        "contradictions": contradictions,
+        "tensions": contradictions,
+        "recommendations": recommendations,
+        "scores": scores,
+        "score_explanations": SCORE_EXPLANATIONS,
+        "quotes_or_salient_sentences": salient_sentences,
+        "categories": structured_categories,
+        "category_counts": dict(category_counts),
+        "keyword_frequencies": keyword_frequencies,
+        "analysis_notes": [
+            "Lecture heuristique locale a partir de signaux lexicaux et structurels.",
+            DISCLAIMER_TEXT,
+        ],
+        "meta": {
+            "word_count": corpus["token_count"],
+            "sentence_count": corpus["sentence_count"],
+            "lexical_diversity": corpus["lexical_diversity"],
+        },
+    }
