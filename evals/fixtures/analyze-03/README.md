# Orders export
`list_orders` returns all non-deleted orders, including archived ones.
`active` is an operational flag and can be false for an archived order.
Export consumers require every non-deleted order exactly once.
Run `python3 -m unittest -v`.
