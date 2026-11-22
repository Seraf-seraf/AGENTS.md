# Order browsing roadmap
S1 (already implemented): each input row has status=open|archived.
S2: list_orders(rows, status=None) returns all rows or exact status matches.
Preserve input order. Input rows must not be mutated.
S3: add --status to the CLI; this is a separate later stage.
Current CLI lists every order. Run `python3 -m unittest -v`.
