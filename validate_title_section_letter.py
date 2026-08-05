# SUPERSEDED 2026-08-05 by validate_title_alphabetical_order.py - do not use
# this script or resurrect its approach. Left in place (not deleted) only so
# the historical PROJECT-STATUS.md references to it still point at a file
# that explains what replaced it.
#
# Why this one was retired: it compared a title's first letter against that
# same klal's own `section` field. That is checking one derived field
# against another derived field, not against ground truth - a klal-boundary
# corruption that shifted both `title` and `section` together would pass
# silently. It also only knew Part 1's 5 section names, so part2.json /
# part3.json were iterated over but every klal in them was silently skipped
# (their `section` values were never in SECTION_LETTER), despite the script
# looking like it covered the whole corpus.
#
# validate_title_alphabetical_order.py checks the title sequence against
# itself (isotonic regression over title-first-letter ranks) - no `section`
# field involved, so it can't inherit a shared corruption, and it covers the
# real klalim_demo_dataset.json sequence directly. Run that one.
raise SystemExit(
    "validate_title_section_letter.py is superseded - run "
    "validate_title_alphabetical_order.py instead (see PROJECT-STATUS.md, "
    "2026-08-05, for why)."
)
