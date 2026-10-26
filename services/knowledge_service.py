"""Load, search, and extend the financial knowledge base.

Search is keyword scoring. It does not generate answers or call a model.
"""

import re
import uuid
from pathlib import Path

from services.storage_service import PROJECT_ROOT, load_json, save_json


KNOWLEDGE_FILE = PROJECT_ROOT / "data" / "knowledge_base.json"

# Common words are ignored for overlap scoring. Negation words such as
# "not" stay in the query because they can change the meaning.
STOP_WORDS = {"what", "is", "my", "the", "a", "an"}


def load_knowledge(file_path=None):
    """Load knowledge records. A missing file returns an empty list."""
    path = Path(file_path) if file_path else KNOWLEDGE_FILE
    records = load_json(path, [])
    if not isinstance(records, list):
        raise ValueError(
            "Knowledge base must be a JSON array. The saved file was not changed."
        )
    return records


def normalize_text(text):
    """Lowercase text and remove punctuation for comparison."""
    text = "" if text is None else str(text)
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def _meaningful_words(normalized_text):
    return [
        word
        for word in normalized_text.split()
        if word not in STOP_WORDS
    ]


def _keyword_phrase_match(normalized_query, keywords):
    """True when the query is a keyword or contains a multi-word keyword."""
    for keyword in keywords:
        if not keyword:
            continue
        if keyword == normalized_query:
            return True
        if len(keyword.split()) >= 2 and keyword in normalized_query:
            return True
    return False


def search_knowledge(query, file_path=None):
    """Rank knowledge records for a question.

    Scoring:
    - exact question match: +10
    - exact keyword, or a full multi-word keyword inside the query: +8
    - each overlapping meaningful word: +1

    Stop words do not add points. A result is kept when the question matches,
    a keyword phrase matches, or at least half of the meaningful query words
    appear in the record. A single shared word in a long question is not enough.
    """
    records = load_knowledge(file_path)
    normalized_query = normalize_text(query)
    if not normalized_query:
        return []

    query_words = _meaningful_words(normalized_query)
    # Generic wording such as "what is the" is not a search.
    if not query_words:
        return []

    results = []
    for record in records:
        question = normalize_text(record.get("question", ""))
        keywords = [
            normalize_text(keyword)
            for keyword in record.get("keywords", [])
        ]
        category = normalize_text(record.get("category", ""))
        searchable_text = " ".join([question, category, *keywords])
        searchable_words = set(_meaningful_words(searchable_text))

        overlap = [
            word
            for word in query_words
            if word in searchable_words
        ]
        exact_question = normalized_query == question
        keyword_phrase = _keyword_phrase_match(normalized_query, keywords)

        score = len(overlap)
        if exact_question:
            score += 10
        if keyword_phrase:
            score += 8
        if score <= 0:
            continue

        coverage = len(overlap) / len(query_words)
        relevant = exact_question or keyword_phrase or coverage >= 0.5
        if not relevant:
            continue

        results.append({
            "record": record,
            "score": score,
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results


def _keyword_list(keywords):
    if isinstance(keywords, str):
        return [
            word.strip()
            for word in keywords.split(",")
            if word.strip()
        ]
    return [
        str(word).strip()
        for word in keywords
        if str(word).strip()
    ]


def add_knowledge(
    category,
    question,
    answer,
    keywords,
    source,
    file_path=None,
):
    """Validate and append one knowledge record."""
    if not str(category).strip():
        raise ValueError("Category is required.")
    if not str(question).strip():
        raise ValueError("Question is required.")
    if not str(answer).strip():
        raise ValueError("Answer is required.")
    if not str(source).strip():
        raise ValueError("Source is required.")

    keyword_list = _keyword_list(keywords)
    if not keyword_list:
        raise ValueError("At least one keyword is required.")

    path = Path(file_path) if file_path else KNOWLEDGE_FILE
    records = load_knowledge(path)
    new_record = {
        "id": f"KB-{uuid.uuid4().hex[:8]}",
        "category": str(category).strip(),
        "question": str(question).strip(),
        "answer": str(answer).strip(),
        "keywords": keyword_list,
        "source": str(source).strip(),
    }
    records.append(new_record)
    save_json(path, records)
    return new_record
