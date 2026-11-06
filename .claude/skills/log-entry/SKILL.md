---
name: log-entry
description: Use whenever scientific work is done in this directory (downloads, new or changed CIF/PDB files, scripts, findings, decisions, validation results). Appends a dated entry to LOG.md before finishing.
---

Append one entry to `LOG.md` (newest at the bottom) before ending your turn:

```
## <output of `date '+%F %H:%M'`> - <short title> (<Claude|user>)
- What: files added/changed (exact names), commands/scripts used
- Source: COD id / DOI / URL, and the `refs.bib` key if any
- Finding: result, quoted from tool output; label anything unchecked as "unverified"
- Next: open questions
```

Rules: run `date '+%F %H:%M'` and paste its output; never type a time by hand. Log what was actually observed, not what was intended. Failed attempts and dead ends go in too. Do not rewrite old entries; add a correction entry instead. Pair with the `add-reference` skill when a peer-reviewed source was used.
