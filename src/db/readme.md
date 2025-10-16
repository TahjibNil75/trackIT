| Option          | Effect                                             |
| --------------- | -------------------------------------------------- |
| `"CASCADE"`     | Delete child rows when parent is deleted           |
| `"SET NULL"`    | Set child’s FK to `NULL` when parent is deleted    |
| `"RESTRICT"`    | Prevent deletion of parent if child rows exist     |
| `"NO ACTION"`   | Similar to `RESTRICT` (default in most databases)  |
| `"SET DEFAULT"` | Set FK to its default value when parent is deleted |
