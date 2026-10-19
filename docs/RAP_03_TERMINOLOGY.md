# RAP-03 downstream terminology

The presentation module maps generic engine kinds to battle vocabulary without
changing the engine, its stable identifiers, enum values or wire schemas. It
covers battle/event/competition, match/stage, emcee/performer, promoter/producer,
judge, round, league/organization, champion/winner and score labels.

Callers must authorize engine data through the RAP-01 boundary before invoking
`presentation(record, kind)`. The returned label is separate from a copied
original record. This module grants no read access and publishes nothing.
`heading(kind, count)` renders only the fixed supported vocabulary, with strict
count validation. Unknown strings, markup, boolean counts and negative counts
are rejected rather than reflected into a page. Do not recursively rename keys
or replace words in user-authored performance text.

Run `python -m unittest discover -s tests -v`. Fixtures verify stable/nested data
preservation, copy independence, unknown-markup rejection and immutable labels.
The current RAP-03 branch does not contain the unmerged RAP-01 application;
rendering these labels inside its authenticated workspace still requires that
foundation integration. No live engine session or production acceptance is
claimed by the standalone formatter tests.
