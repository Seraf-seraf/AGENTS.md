# Payment adapter (local model)
The gateway records an operation before replying. Network timeout may happen
after that record. Same request_id returns the original result without a new charge.
`lookup(request_id)` can reconcile the operation. Never contact external services.
`python3 -m unittest -v` checks the local accepted behavior.
