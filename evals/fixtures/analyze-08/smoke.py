from pathlib import Path
assert "external_id" in Path("migration.sql").read_text()
print("Local SQL artifact exists")
