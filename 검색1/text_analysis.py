from collections import Counter


def build_full_text(docs: list[dict]) -> str:
    parts = []

    for doc in docs:
        title = (doc.get("title") or "").strip()
        snippet = (doc.get("snippet") or "").strip()
        content = (doc.get("content") or "").strip()

        if title:
            parts.append(title)
        if snippet:
            parts.append(snippet)
        if content:
            parts.append(content)

    return "\n".join(parts)


def count_occurrences_per_doc(docs: list[dict], alias_map: dict[str, str]) -> Counter:
    counter = Counter()

    for doc in docs:
        text = "\n".join(
            part.strip()
            for part in [
                doc.get("title") or "",
                doc.get("snippet") or "",
                doc.get("content") or "",
            ]
            if part and part.strip()
        )

        if not text:
            continue

        seen_canonicals = set()

        for alias, canonical in alias_map.items():
            if canonical in seen_canonicals:
                continue

            if alias in text:
                counter[canonical] += 1
                seen_canonicals.add(canonical)

    return counter


def format_counter_all(counter: Counter) -> str:
    if not counter:
        return "모름"

    items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return " / ".join(f"{name}({count})" for name, count in items)
