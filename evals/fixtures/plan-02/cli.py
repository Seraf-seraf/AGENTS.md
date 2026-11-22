import json
import sys
from orders import list_orders


def main():
    rows = json.load(sys.stdin)
    print(json.dumps(list_orders(rows)))


if __name__ == "__main__":
    main()
