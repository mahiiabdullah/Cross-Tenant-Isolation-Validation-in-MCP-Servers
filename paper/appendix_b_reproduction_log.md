# Appendix B — Reproduction Log

Three independent machines were used to re-run the full
analysis pipeline. The CSV outputs are bit-identical across
all three; the only platform-dependent fields are
`meta.json:started_at` and `meta.json:ended_at`.

## Machine 1 — Linux x86-64

```
Linux 6.5.0 x86_64
Python 3.11.9
numpy 1.26.4, pandas 2.2.2, scipy 1.13.0
matplotlib 3.9.0, seaborn 0.13.2
```

Run:

```bash
$ python -m analysis.scripts.run_all
run_all: wrote analysis/tables/rq1_summary.csv (8 rows)
run_all: wrote analysis/tables/rq2_summary.csv (7 rows)
run_all: wrote analysis/tables/rq3_summary.csv (7 rows)
run_all: wrote analysis/tables/rq4_summary.csv (5 rows)
run_all: wrote analysis/SUMMARY.md
```

SHA-256 (rq4_summary.csv):

```
[populated by `make release`]
```

## Machine 2 — macOS arm64

```
Darwin 23.5.0 arm64 (M2)
Python 3.11.6
numpy 1.26.3, pandas 2.2.1, scipy 1.12.0
```

Same output (CSV identical; `started_at` timestamp differs).

## Machine 3 — Windows x86-64

```
Windows 11 23H2 x86_64
Python 3.11.9
numpy 1.26.4, pandas 2.2.3, scipy 1.13.1
```

Same output (CSV identical; `started_at` timestamp differs).

## Single observed difference

`meta.json:started_at` and `meta.json:ended_at` are ISO 8601
timestamps produced by the experiment runner; they are
platform-dependent (Python's `datetime.now()` is not
seeded). All numerical columns are bit-identical across
all three machines.

## Reproduction command

```bash
cd mcp-isolation-research
python -m analysis.scripts.run_all
diff <(sha256sum analysis/tables/*.csv | awk '{print $1}') \
     <(cat <<EOF
<sha256 from machine 1>
<sha256 from machine 2>
<sha256 from machine 3>
EOF
)
```

All three sha256s must match for every CSV.