# Delivery fee
Accepted extension: support pickup orders with fee 0; delivery behavior stays
200 cents up to and including 1000 grams, otherwise 400 cents.
Public function: `fee(weight_grams, pickup=False)` after the extension.
Run `python3 -m unittest -v`.
