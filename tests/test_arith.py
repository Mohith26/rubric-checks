from rubric_arith import check_text, duplicate_pairs


def test_flags_the_inconsistent_example_from_the_rift_post():
    text = "e.g. USD short rate - EUR short rate - cross currency basis = 5.0% - 3.0% - 3.0% = 1.8% per year"
    [f] = check_text(text)
    assert f.stated == 1.8
    assert f.computed == -1.0


def test_accepts_correct_arithmetic_and_rounding():
    assert check_text("profit = 120 - 45.5 = 74.5") == []
    assert check_text("margin is 2 / 3 = 0.67") == []
    assert check_text("1,200 x 3 = 3,600 units") == []
    assert check_text("grows 10% x 50 = 5 points") == []


def test_flags_wrong_products_and_sums():
    assert len(check_text("total = 12 + 30 = 52")) == 1
    assert len(check_text("dose is 70 x 2 = 120 mg")) == 1


def test_approx_uses_looser_tolerance():
    assert check_text("about 100 / 3 \u2248 33") == []


def test_skips_ambiguous_text():
    assert check_text("score 5-10 = good") == []  # a range, not subtraction
    assert check_text("$5M - 300k = 4.7") == []  # mixed units
    assert check_text("2x3 = 7") == []  # unspaced x
    assert check_text("(4 + 2) * 3 = 18") == []  # parentheses are not parsed


def test_duplicate_pairs():
    crits = [
        "States that the minimum beat in new store openings is 3.75%",
        "States that the maximum beat in new store openings is 3.75%",
        "Recommends a follow up visit within two weeks",
    ]
    assert duplicate_pairs(crits, threshold=0.8) == [(0, 1, 0.833)]
    assert duplicate_pairs(crits) == []


def test_scale_suffixes_and_trailing_punctuation():
    assert check_text("releases exactly $168,000 ($24M \u00d7 0.7% = $168,000).") == []
    assert check_text("tax is 20% x 40% x $4m = $320,000.") == []
    assert check_text("share is $41,667 \u00d7 30% = $12,500.") == []
    assert check_text("ratio = 12 / 220 \u2248 5.5%.") == []


def test_skips_tails_of_longer_expressions_and_scientific_notation():
    assert check_text("(28% - 12%) \u00d7 50% \u00d7 $500m = $40m notional") == []
    assert check_text("0.5\u00d7(-\u00a35.0m) + 0.5\u00d7\u00a30 = -\u00a32.5m") == []
    assert check_text("a = 1/1100=9.091\\times10^{-4}") == []


def test_flags_an_order_of_magnitude_slip():
    [f] = check_text("instant hit (e.g., 0.025 * 0.4 * 0.25 = 2.5% of EBITDA)")
    assert f.stated == 2.5


def test_result_scale_with_plain_operands():
    assert check_text("FCF = 65 \u2212 25 \u2212 28 = 12m") == []
    [f] = check_text("tax such as \u00a344.5*25%= \u00a311.25m")
    assert round(f.computed, 3) == 11.125
