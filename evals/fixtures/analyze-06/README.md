# Local worker CLI state
A shared device has one owner. `cancel` requests cleanup; the device remains
occupied until `cleanup_complete`. Another start must fail while occupied.
`status` is always available, including cancellation. No UI exists.
Run `python3 -m unittest -v`.
