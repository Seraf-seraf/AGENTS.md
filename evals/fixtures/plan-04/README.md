# Order notification
submit(order, store, services) persists the order and emits order_created through
the project's notification service with payload {'order_id': order['id']}.
The supplied services object belongs to the application composition root.
Run `python3 -m unittest -v`.
