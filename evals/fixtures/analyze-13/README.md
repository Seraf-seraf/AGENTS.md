# Order API
Existing `list_orders(rows)` returns dictionaries with id.
Requested extension: every result also has `status`; optional status=None returns
all rows, status="open" or "archived" returns exactly the matching records.
Preserve input order and do not mutate input dictionaries.
Run `python3 -m unittest -v`.
