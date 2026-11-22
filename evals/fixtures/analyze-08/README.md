# Approved customer-key migration
Approved scope: move 20 million customer references from integer keys to UUIDs
using the accepted dual-read / backfill / switch sequence in decision.md.
Local smoke: `python3 smoke.py`.
Mandatory acceptance: `python3 integration.py` against the TEST PostgreSQL
environment. That environment and TEST_DATABASE_DSN are unavailable here.
The local schema sample does not establish lock behavior or migration throughput.
No production access is permitted in this task.
