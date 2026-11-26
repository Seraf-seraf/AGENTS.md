# Durable local outbox
Requirement: each saved order has a durable notification task in the same
SQLite transaction. Delivery is at least once. The receiver deduplicates by id.
Current load: 10 tasks/minute; measured capacity: 200 tasks/minute.
p99 delivery delay: 0.4 seconds; requirement: below 5 seconds.
A single worker is sufficient; cross-region delivery is not required.
`connect()` opens `outbox.sqlite3` in the current directory; pass a database path
to reopen a store elsewhere. Tests use temporary directories for their databases.
Run `python3 -B -m unittest -v`.
