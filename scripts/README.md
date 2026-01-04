# my-grid Scripts

Ready-to-use automation scripts for the my-grid API.

## Prerequisites

Start my-grid with server mode enabled:

```bash
python mygrid.py --server
```

## Available Scripts

### Python Scripts

| Script              | Description                        |
| ------------------- | ---------------------------------- |
| `mygrid_client.py`  | Reusable Python client library     |
| `import_csv.py`     | Import CSV data as table on canvas |
| `generate_grid.py`  | Generate coordinate grid lines     |
| `batch_commands.py` | Execute commands from a file       |

### Bash Scripts

| Script        | Description                    |
| ------------- | ------------------------------ |
| `mygrid-send` | Send single command to my-grid |
| `mygrid-pipe` | Pipe stdin to canvas region    |

## Quick Examples

### Python

```python
from mygrid_client import MyGridClient

client = MyGridClient()
client.goto(0, 0)
client.text('Hello World!')
client.rect(20, 10)
```

### Bash

```bash
# Single command
./mygrid-send ':text Hello'

# Pipe output
ls -la | ./mygrid-pipe 0 0

# Batch commands
./batch_commands.py commands.txt
```

## See Also

- [API Scripting Guide](../docs/guides/api-scripting.md) - Full documentation
- [Zones Reference](../docs/guides/zones-reference.md) - Zone commands
