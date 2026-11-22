# Receipt delivery
S1: totals.total_cents(items) sums price_cents * quantity, empty list gives 0.
S2 depends on S1: receipt.render(items) returns {'total_cents': sum, 'lines': len(items)}.
S3 is future context: CSV export in csv_export.py. It is not required for S1/S2.
Only nonnegative integer prices and positive integer quantities are accepted input
in this release; validation of other inputs is not requested.
Local verification command: `python3 -m unittest -v`.
