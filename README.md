# arabic-nlp-toolkit

Small, **dependency-free** Python helpers for the parts of Arabic text processing that quietly break search, matching and speech scoring.

Two Arabic strings that look identical often aren't byte-identical: optional diacritics, the tatweel stretch, four kinds of alef, alef maksura vs. ya, two digit systems, invisible direction marks from copy-paste, and ligature characters from PDFs. This toolkit folds those differences together, then gives you tokenising, fuzzy matching and word alignment that understand them.

```python
from arabic_toolkit import normalize, similarity, tokenize, to_buckwalter

normalize("أَهْلاً وَسَهْلاً بِكُمْ")       # 'اهلا وسهلا بكم'
normalize("كـــتاب ١٢٣؟")                 # 'كتاب 123?'
similarity("احمد", "أَحْمَد")              # 1.0
tokenize("قرأتُ كتاباً عن AI في 2026")      # ['قرأتُ', 'كتاباً', 'عن', 'AI', 'في', '2026']
to_buckwalter("كَتَبَ")                   # 'kataba'
```

## What `normalize` does

Each rule is a keyword argument you can switch off.

| Rule | Example | Default |
|---|---|---|
| Strip diacritics (harakat, shadda, sukun, tanween, Quranic marks) | مُحَمَّد → محمد | on |
| Remove tatweel | كـــتاب → كتاب | on |
| Unify alef forms | أ إ آ ٱ → ا | on |
| Alef maksura → ya | مصطفى → مصطفي | on |
| Arabic-Indic and Persian digits → ASCII | ١٢٣ ۴۵ → 123 45 | on |
| Arabic punctuation → ASCII | ؟ ، ؛ → ? , ; | on |
| Remove invisible characters (RLM, ZWNJ, BOM...) | | on |
| Fold presentation forms (PDF ligatures) | ﻻ → لا | on |
| Ta marbuta → ha | مدرسة → مدرسه | **off** |
| Hamza carriers → base letter | مسؤول → مسوول | **off** |

The last two merge words that can differ in meaning, so they're off by default. `normalize_loose()` turns everything on, for comparing noisy text such as speech-to-text or OCR output against a reference.

Text is composed to Unicode NFC first, so a letter typed as two code points (base + combining hamza) is handled the same as the precomposed letter.

## Matching and alignment

```python
from arabic_toolkit import best_match, align, word_error_rate

best_match("ابوظبى", ["دبي", "أبوظبي", "الشارقة"])   # ('أبوظبي', 1.0)

ref = "the cat sat on the mat".split()
hyp = "the cat sit on mat today".split()
word_error_rate(ref, hyp)                            # 0.5
[op.kind for op in align(ref, hyp)]
# ['equal', 'equal', 'substitute', 'equal', 'delete', 'equal', 'insert']
```

`align` returns a minimum-edit alignment, and among equally short alignments picks the one with the most exact matches. It reports the skipped "the" as a deletion rather than hiding it inside a chain of substitutions, which matters when you use the alignment to find missed words ([speech-scorer](https://github.com/AmeesAnsari/speech-scorer) does).

## Command line

```bash
python -m arabic_toolkit normalize "أَهْلاً وَسَهْلاً"     # اهلا وسهلا
python -m arabic_toolkit loose "مسؤولية"                  # مسووليه
python -m arabic_toolkit tokens "النص الكامل هنا"
echo "كَتَبَ" | python -m arabic_toolkit buckwalter       # kataba
```

## Install

```bash
pip install git+https://github.com/AmeesAnsari/arabic-nlp-toolkit
```

Python 3.9+, standard library only.

## Tests

```bash
pip install pytest && pytest -q
```

24 tests. Every expectation is written with explicit Unicode code points, so no test depends on how an editor renders Arabic. One property test checks 200 random sequence pairs: each alignment must rebuild both sequences and use exactly the minimum number of edits.

## Scope

This is deliberately small: normalisation, tokenising, transliteration and matching. For morphology (roots, stemming, POS tagging), use [CAMeL Tools](https://github.com/CAMeL-Lab/camel_tools).

## License

MIT
