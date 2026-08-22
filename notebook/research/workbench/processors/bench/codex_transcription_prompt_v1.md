# Codex Civic Transcription Prompt v1

You are performing bounded document representation processing, not civic
interpretation. Transcribe only the selected image pages supplied with this
request.

Rules:

- Return exact visible text; do not summarize or explain.
- Preserve visible reading order and page identity.
- Do not normalize names, numbers, punctuation or accents unless the pixels show
  them that way.
- Do not infer election results, political meaning, entities, relations or civic
  semantics.
- Do not invent unreadable text. Put a short description in `uncertain_spans`
  and leave the transcription faithful to visible evidence.
- Return only data valid under the supplied JSON Schema.
- Put table rows in `tables` only when visible structure supports them.

The page IDs are supplied in the image filenames. Use the filename stem without
the `.png` extension as `page_id` (for example, `clean_scan_300.png` becomes
`clean_scan_300`). Process every supplied image exactly once.
