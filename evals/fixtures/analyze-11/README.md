# Amount formatting
`format_cents` accepts an integer number of cents, including zero and negatives,
and returns an ASCII decimal string with exactly two digits after the point.
It must remain exact for arbitrarily large Python integers.
Booleans and non-integers raise TypeError. Run `python3 -m unittest -v`.
