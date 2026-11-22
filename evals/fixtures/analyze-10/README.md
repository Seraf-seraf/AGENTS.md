# Transactional order email
Creating an order must not wait for the email server. Once an order is committed,
its notification must survive restart and be retried. Duplicate transport delivery
is allowed only with the same message id; the receiver deduplicates that id.
SQLite is already used and can hold orders and an outbox in one transaction.
Current volume is 3 orders/minute. No new external service is currently deployed.
Run `python3 -m unittest -v`.
