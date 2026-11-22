# Label service
Python 3, standard library only. Run `python3 -m unittest -v`.
`labels.display_name` is the only public entry point. Its callers require
whitespace to be trimmed and runs of whitespace joined by a single space.
`_normalize` is private; all callers are in labels.py.
