# Historical materials

The current paper is the real-recording DCCR study linked from `../START_HERE.md`.

- `legacy_manuscripts/` preserves the superseded synthetic SCCR manuscripts, numerical templates, citation map, the earlier controlled-evaluation archive, and previous entry-point/reproduction instructions.
- `legacy_document_qa/` preserves their old rendered previews and document checks.
- `cleanup_manifest.json` records moved artifacts and hashes of the old manuscripts.

The original raw recordings, source reference documents and all frozen synthetic data/model/evaluation files remain in their original directories. They were not deleted or rewritten. The old synthetic results must not be pooled with the new field-study results.

Legacy manuscript builders expect their former `paper/` input paths. To rebuild a historical manuscript, restore its archived inputs only in a separate project copy and follow `legacy_manuscripts/EXPERIMENT_README_previous.md`. Current manuscript sources are `paper/field_en.md` and `paper/field_zh.md`; current builders are `code/finalize_field_paper.py` and `code/build_field_documents.py`.
