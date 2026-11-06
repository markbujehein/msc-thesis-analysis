---
name: add-reference
description: Use whenever a file is downloaded and kept, or a fact is taken from a peer-reviewed source (paper, SI, database entry that has a primary publication). Adds the BibLaTeX entry to refs.bib.
---

For every kept download or sourced fact from a peer-reviewed publication:

1. Add a BibLaTeX entry to `refs.bib` (skip if the key already exists). Key format: `firstauthorYEAR` (e.g. `salager2010`). Include author, title, journaltitle, year, volume, pages, doi.
2. Take the metadata from the paper/CIF/publisher page itself. If a field was not seen in a source, do not guess: add `note = {UNVERIFIED: <field>}`.
3. For database files (COD, CSD) cite the primary publication of the entry and the database paper; put the entry id in `note`.
4. Add the key to the `Source:` line of the matching `LOG.md` entry.

Non-peer-reviewed sources (vendor pages, wikis) are not added to `refs.bib`; mention them in `LOG.md` only.
