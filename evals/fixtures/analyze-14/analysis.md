# Prior analysis, accepted in this conversation
API uses optional status: open|archived|null. null omits the status filter and
returns all non-deleted records. Export uses null. This is a product requirement,
not a synonym for status=open. Deleted records are excluded by a separate rule.
