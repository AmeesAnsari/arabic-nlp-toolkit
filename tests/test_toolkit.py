"""Tests use explicit code points (via chr / \\u escapes) so every expectation is unambiguous."""

import unicodedata

import pytest

from arabic_toolkit import (align, arabic_ratio, best_match, from_buckwalter, is_arabic, levenshtein,
                            normalize, normalize_loose, similarity, strip_diacritics, to_buckwalter,
                            tokenize, word_error_rate)

KITAB = "\u0643\u062a\u0627\u0628"  # كتاب "book"
ALEF = "\u0627"


# ---------------------------------------------------------------- normalize


def test_strips_diacritics_and_shadda():
    # مُحَمَّد -> محمد
    voweled = "\u0645\u064f\u062d\u064e\u0645\u0651\u064e\u062f"
    assert strip_diacritics(voweled) == "\u0645\u062d\u0645\u062f"


def test_strips_tanween_and_superscript_alef():
    # كتابًا -> كتابا ; هٰذا -> هذا
    assert normalize(KITAB + ALEF[0] + "\u064b") == KITAB + ALEF
    assert normalize("\u0647\u0670\u0630\u0627") == "\u0647\u0630\u0627"


def test_removes_tatweel():
    assert normalize("\u0643\u0640\u0640\u0640\u062a\u0627\u0628") == KITAB


@pytest.mark.parametrize("variant", ["\u0622", "\u0623", "\u0625", "\u0671"])
def test_alef_variants_fold_to_bare_alef(variant):
    assert normalize(variant + "\u062d\u0645\u062f") == ALEF + "\u062d\u0645\u062f"


def test_alef_maksura_to_ya_by_default_only():
    word = "\u0645\u0635\u0637\u0641\u0649"  # مصطفى
    assert normalize(word).endswith("\u064a")
    assert normalize(word, alef_maksura=False).endswith("\u0649")


def test_ta_marbuta_and_hamza_are_opt_in():
    madrasa = "\u0645\u062f\u0631\u0633\u0629"  # مدرسة
    assert normalize(madrasa) == madrasa
    assert normalize(madrasa, ta_marbuta=True).endswith("\u0647")
    masul = "\u0645\u0633\u0624\u0648\u0644"  # مسؤول
    assert normalize(masul) == masul
    assert normalize_loose(masul) == "\u0645\u0633\u0648\u0648\u0644"


def test_decomposed_hamza_is_composed_not_stripped():
    # و + combining hamza above (U+0654) is the same text as ؤ (U+0624); it must not lose its hamza.
    decomposed = "\u0645\u0633\u0648\u0654\u0648\u0644"
    assert unicodedata.normalize("NFC", decomposed) != decomposed
    assert normalize(decomposed) == "\u0645\u0633\u0624\u0648\u0644"


def test_digits_and_punctuation():
    assert normalize("\u0661\u0662\u0663 \u06f4\u06f5") == "123 45"
    assert normalize("\u0645\u0631\u062d\u0628\u0627\u061f\u060c") == "\u0645\u0631\u062d\u0628\u0627?,"


def test_invisible_characters_and_whitespace():
    noisy = "\ufeff\u200f" + KITAB + "\u200c  \n " + KITAB + "\u200e"
    assert normalize(noisy) == KITAB + " " + KITAB


def test_presentation_forms_from_pdfs():
    # U+FEFB is the lam-alef ligature; PDFs often contain it instead of two letters.
    assert normalize("\ufefb") == "\u0644\u0627"


def test_latin_text_untouched_except_whitespace():
    assert normalize("  Hello,   World ") == "Hello, World"


# ---------------------------------------------------------------- text


def test_tokenize_mixed_text():
    text = "\u0642\u0631\u0623\u062a " + KITAB + "\u064b\u0627 \u0639\u0646 AI \u0641\u064a 2026\u060c \u0661\u0662."
    assert tokenize(text) == ["\u0642\u0631\u0623\u062a", KITAB + "\u064b\u0627", "\u0639\u0646", "AI",
                              "\u0641\u064a", "2026", "\u0661\u0662"]


def test_arabic_ratio():
    assert arabic_ratio(KITAB) == 1.0
    assert arabic_ratio("abc") == 0.0
    assert arabic_ratio(KITAB + " book") == 0.5
    assert is_arabic(KITAB + " ok") and not is_arabic("123")


def test_buckwalter_round_trip():
    # كَتَبَ -> kataba ; مُدَرِّسَة -> mudar~isap
    assert to_buckwalter("\u0643\u064e\u062a\u064e\u0628\u064e") == "kataba"
    voweled = "\u0645\u064f\u062f\u064e\u0631\u0651\u0650\u0633\u064e\u0629"
    assert to_buckwalter(voweled) == "mudar~isap"
    assert from_buckwalter(to_buckwalter(voweled)) == voweled


def test_buckwalter_table_is_one_to_one():
    from arabic_toolkit.text import BUCKWALTER
    assert len(set(BUCKWALTER.values())) == len(BUCKWALTER)


# ---------------------------------------------------------------- match


def test_levenshtein():
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein([], ["a"]) == 1
    assert levenshtein(["a", "b"], ["a", "b"]) == 0


def test_similarity_ignores_diacritics_and_alef_forms():
    plain = ALEF + "\u062d\u0645\u062f"  # احمد
    fancy = "\u0623\u064e\u062d\u0652\u0645\u064e\u062f"  # أَحْمَد
    assert similarity(plain, fancy) == 1.0
    assert similarity(plain, fancy, normalizer=None) < 1.0


def test_best_match():
    cities = ["\u062f\u0628\u064a", "\u0623\u0628\u0648\u0638\u0628\u064a", "\u0627\u0644\u0634\u0627\u0631\u0642\u0629"]
    query = "\u0627\u0628\u0648 \u0638\u0628\u0649"  # "ابو ظبى": spacing, bare alef and alef maksura differ
    match = best_match(query.replace(" ", ""), cities)
    assert match[0] == cities[1] and match[1] == 1.0
    assert best_match("zzz", cities, min_score=0.5) is None


def test_align_and_wer():
    ref = "the cat sat on the mat".split()
    hyp = "the cat sit on mat today".split()
    ops = align(ref, hyp)
    # Ties are broken toward more matches: "the" (2nd) deleted, "mat" matched, "today" inserted.
    assert [op.kind for op in ops] == ["equal", "equal", "substitute", "equal", "delete", "equal", "insert"]
    assert ops[4].ref_index == 4 and ref[ops[4].ref_index] == "the"
    assert word_error_rate(ref, hyp) == pytest.approx(3 / 6)


def test_align_is_a_valid_minimum_edit_path():
    import random
    rng = random.Random(7)
    for _ in range(200):
        ref = [rng.choice("abcd") for _ in range(rng.randint(0, 8))]
        hyp = [rng.choice("abcd") for _ in range(rng.randint(0, 8))]
        ops = align(ref, hyp)
        # Replaying the ops must reconstruct both sequences, with exactly levenshtein() edits.
        assert [ref[o.ref_index] for o in ops if o.ref_index is not None] == ref
        assert [hyp[o.hyp_index] for o in ops if o.hyp_index is not None] == hyp
        assert sum(o.kind != "equal" for o in ops) == levenshtein(ref, hyp)
        assert all(ref[o.ref_index] == hyp[o.hyp_index] for o in ops if o.kind == "equal")
    assert word_error_rate([], []) == 0.0 and word_error_rate(ref, ref) == 0.0


def test_cli_normalize(capsys):
    from arabic_toolkit.__main__ import main
    main(["normalize", "\u0623\u064e\u0647\u0652\u0644\u0627\u064b"])
    assert capsys.readouterr().out.strip() == ALEF + "\u0647\u0644\u0627"
