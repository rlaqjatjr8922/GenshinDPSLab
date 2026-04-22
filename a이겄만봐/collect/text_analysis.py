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


def count_occurrences_per_doc(
    docs: list[dict],
    alias_group_map: dict[str, list[str]],
    top_k: int | None = None,
) -> Counter:
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
        ).lower()

        if not text:
            continue

        matched = []

        for canonical, aliases in alias_group_map.items():
            if not isinstance(aliases, list):
                continue

            for alias in aliases:
                alias_norm = alias.strip().lower()
                if alias_norm and alias_norm in text:
                    matched.append(canonical)
                    break

        if top_k is not None:
            matched = matched[:top_k]

        for canonical in matched:
            counter[canonical] += 1

    return counter


def format_counter_all(counter: Counter) -> str:
    if not counter:
        return "모름"

    items = sorted(counter.items(), key=lambda x: (-x[1], x[0]))
    return " / ".join(f"{name}({count})" for name, count in items)