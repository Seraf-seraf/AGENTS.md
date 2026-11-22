import sqlite3


def connect():
    connection = sqlite3.connect(":memory:")
    connection.executescript("CREATE TABLE orders(id TEXT PRIMARY KEY); CREATE TABLE tasks(id TEXT PRIMARY KEY, done INTEGER DEFAULT 0);")
    return connection


def save_order(connection, order_id):
    with connection:
        connection.execute("INSERT INTO orders VALUES (?)", (order_id,))
        connection.execute("INSERT INTO tasks(id) VALUES (?)", (order_id,))


def deliver(connection, receiver):
    for (task_id,) in connection.execute("SELECT id FROM tasks WHERE done=0"):
        receiver.send_once(task_id)
        with connection:
            connection.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
