# Tenant documents API
Every endpoint uses session.tenant_id as the access scope. A caller must never
receive another tenant's document, list row, or attachment. `get_document`
and `download_attachment` raise PermissionError for another tenant.
There are no new modules in the change. Run `python3 -m unittest -v`.
