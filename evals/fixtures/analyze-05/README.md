# Order checkout
Saving the order is required. Analytics is optional and its outage must not
prevent saving. Analytics failures must remain distinguishable from success.
The store and analytics do not share a transaction.
Run `python3 -m unittest -v`.
