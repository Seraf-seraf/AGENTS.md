# Status route, partial earlier work
S1: resolve('/status') returns {'status':'ok'}; any unknown route raises KeyError.
Earlier work already registered the route in api.py; regression tests for the
contract are still missing. Keep the same route identity and do not add another.
Run `python3 -m unittest -v`.
