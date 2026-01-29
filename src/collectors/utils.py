import re
from config import (
    ALL_KEYWORDS_SET,
    KEYWORD_CATEGORIES,
    VALID_CATEGORIES,
    WORD_TO_TECH_REMAP,
)


def clean_html(text):
    """Nettoyer le HTML du texte"""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean)
    clean = clean.replace("&nbsp;", " ").replace("&amp;", "&")
    clean = clean.replace("&lt;", "<").replace("&gt;", ">")
    clean = clean.replace("&quot;", '"').replace("&#x27;", "'").replace("&#39;", "'")
    return clean.strip()


def is_tech_keyword(word):
    """Vérifier si un mot est un keyword tech"""
    return word.lower() in ALL_KEYWORDS_SET


def remap_content(text):
    """Remapper le contenu et retourner (new_content, old_content, original_kw, mapped_kw, categories, categorized, is_remapped)"""
    if not text:
        return "", None, [], [], [], {}, False

    text_lower = text.lower()
    words = text_lower.split()
    original_keywords, mapped_keywords = [], []
    categories, categorized = set(), {}
    is_remapped = False
    replacements = {}

    for kw in ALL_KEYWORDS_SET:
        pattern = rf"\b{re.escape(kw)}\b"
        if re.search(pattern, text_lower, re.IGNORECASE):
            original_keywords.append(kw)
            mapped_keywords.append(kw)
            for cat, cat_words in KEYWORD_CATEGORIES.items():
                if kw in cat_words and cat in VALID_CATEGORIES:
                    categories.add(cat)
                    categorized.setdefault(cat, []).append(kw)
                    break

    if len(original_keywords) < 2:
        for word in words:
            clean_word = word.strip(".,!?;:'\"()[]{}").lower()
            if clean_word in WORD_TO_TECH_REMAP:
                tech_word = WORD_TO_TECH_REMAP[clean_word]
                original_keywords.append(clean_word)
                mapped_keywords.append(tech_word)
                replacements[clean_word] = tech_word
                is_remapped = True
                for cat, cat_words in KEYWORD_CATEGORIES.items():
                    if tech_word in cat_words and cat in VALID_CATEGORIES:
                        categories.add(cat)
                        categorized.setdefault(cat, []).append(tech_word)
                        break

    if is_remapped:
        new_content = text
        for old_word, new_word in replacements.items():
            new_content = re.sub(
                rf"\b{old_word}\b", new_word, new_content, flags=re.IGNORECASE
            )
        return (
            new_content,
            text,
            original_keywords,
            mapped_keywords,
            list(categories),
            categorized,
            is_remapped,
        )

    return (
        text,
        None,
        original_keywords,
        mapped_keywords,
        list(categories),
        categorized,
        is_remapped,
    )


def get_keywords_count():
    return len(ALL_KEYWORDS_SET)


def get_remap_count():
    return len(WORD_TO_TECH_REMAP)
