# Durable local outbox
Requirement: each saved order has a durable notification task in the same
SQLite transaction. Delivery is at least once. The receiver deduplicates by id.
Current load: 10 tasks/minute; measured capacity: 200 tasks/minute.
p99 delivery delay: 0.4 seconds; requirement: below 5 seconds.
A single worker is sufficient; cross-region delivery is not required.
Run `python3 -m unittest -v`.
