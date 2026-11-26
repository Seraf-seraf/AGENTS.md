# Amount label
S1: change format_total(cents) to 'USD <decimal>' with two fractional digits,
exact for integer cents. Examples: 1 -> 'USD 0.01', -101 -> 'USD -1.01'.
APP_LOCALE and APP_TITLE are separate colleague-owned changes in the same file.
The locale change is already staged; the title change is only in the working tree.
Preserve each change in its existing Git state and exclude both from the S1 commit.
Assigned paths for S1 are app.py and test_app.py; only the formatting change
and related tests belong to the local S1 commit.
Run `python3 -m unittest -v`.
