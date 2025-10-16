| Option          | Effect                                             |
| --------------- | -------------------------------------------------- |
| `"CASCADE"`     | Delete child rows when parent is deleted           |
| `"SET NULL"`    | Set child’s FK to `NULL` when parent is deleted    |
| `"RESTRICT"`    | Prevent deletion of parent if child rows exist     |
| `"NO ACTION"`   | Similar to `RESTRICT` (default in most databases)  |
| `"SET DEFAULT"` | Set FK to its default value when parent is deleted |




| Structure Type              | Path               | Needs `__init__.py` imports? | Why                                                              |
| --------------------------- | ------------------ | ---------------------------- | ---------------------------------------------------------------- |
| Single `models.py` file     | `src/db/models.py` | ❌ No                         | Python directly loads the module, all names are local            |
| Folder-based models package | `src/db/models/`   | ✅ Yes                        | Python only runs `__init__.py` — you must re-export the contents |
