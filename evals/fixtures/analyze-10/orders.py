def create_order(connection, mailer, order_id):
    with connection:
        connection.execute("INSERT INTO orders VALUES (?)", (order_id,))
    mailer.send(order_id)
