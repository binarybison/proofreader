# Examples gallery

Worked examples showing what Proofreader catches on published papers with known correctness issues. Each example is a faithful reproduction of the kind of output the plugin produces, drawn from the underlying research corpus, presented in a form suitable for new users to evaluate what the tool will do for them.

## Why a gallery

Two purposes:

1. **For new users**: read a single example end-to-end in 10 minutes; decide whether the tool is worth running on your own work.
2. **For contributors**: model for what a good case study looks like. If you run Proofreader on a paper with a known publicly-acknowledged flaw — and the tool catches it — a writeup makes a strong contribution back to the gallery.

## What's in each case

A typical case directory contains:

| File | What it shows |
|---|---|
| `README.md` | The paper, the known issue, what Proofreader caught, links to public material (errata, retraction notices, author acknowledgements) |
| `audit-excerpt.md` | A representative excerpt from the `audit-proof` output — the issues, severity, two-axis verdict |
| `counterexample-excerpt.md` | The counterexample the agent constructed, with parameters and verification method |
| `verification-script.py` | The actual Python the counterexample agent wrote, with comments. Demonstrates that the artifact is genuinely reproducible. |
| `arbiter-verdict.md` | The arbiter's final adjudication if the case was stress-tested |
| `paper-context-excerpt.md` | (Optional) what `prepare-paper-context` produced — useful for showing LaTeX-source advantages |

## Existing cases

| Case | Paper | Flaw type | Severity |
|---|---|---|---|
| [`baruah-rtns-2020-ilp`](baruah-rtns-2020-ilp/) | S. Baruah, *Schedulability Analysis Using ILP*, RTNS 2020 | missing_precondition | unsafe_bound |

## Discretion about subjects

Examples in this gallery are drawn exclusively from **papers whose flaw is already publicly acknowledged** (via a published errata, retraction, journal correction, or the authors' own follow-up paper). Proofreader is a tool for finding correctness issues; surfacing those issues in a public example registry should be done only when the affected community has already had the chance to respond. The gallery is not a venue for "gotcha" demonstrations.

If you run Proofreader on a paper and want to contribute a case study, two paths:

1. **The flaw is already publicly acknowledged.** Build the case study referencing the public material. Welcome contributions.
2. **The flaw appears to be real but is not publicly acknowledged.** Do not contribute it to the gallery. The right next step is private outreach to the authors — they may have already addressed it, may issue an erratum, or may explain why the audit is incorrect.

## Contributing a case

1. Fork the repo, add a new `examples/<short-name>/` directory.
2. Include the six files above (some optional). Keep each one short — the goal is a 10-minute read end-to-end.
3. Cite the original paper canonically. Cite the public errata / acknowledgement / follow-up.
4. Submit a PR with a one-paragraph note describing why this case is instructive (which Proofreader pattern caught it, what an author would learn).

Cases that are accepted into the gallery may be referenced from the methodology paper and from the main README.
