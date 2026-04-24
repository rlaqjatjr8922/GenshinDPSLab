def distribute_tokens(
    total_tokens: int,
    party: list[str],
    main_dps_idx: int,
) -> dict[str, int]:

    n = len(party)

    # 1. 전원 1개씩
    split = {ch: 1 for ch in party}

    remaining = total_tokens - n
    if remaining <= 0:
        return split

    max_per_char = total_tokens // 2
    main_char = party[main_dps_idx]

    # 2. 메인딜러 우선 배정 (50%)
    main_extra = remaining // 2
    addable = max_per_char - split[main_char]

    actual_main_extra = min(main_extra, addable)
    split[main_char] += actual_main_extra
    remaining -= actual_main_extra

    # 3. 나머지 균등 분배
    others = [ch for i, ch in enumerate(party) if i != main_dps_idx]

    while remaining > 0:
        progressed = False

        for ch in others:
            if remaining <= 0:
                break

            if split[ch] < max_per_char:
                split[ch] += 1
                remaining -= 1
                progressed = True

        # 메인도 추가 가능하면 추가
        if remaining > 0 and split[main_char] < max_per_char:
            split[main_char] += 1
            remaining -= 1
            progressed = True

        if not progressed:
            break

    return split