# V3 fixture frontend

Minimal static board layout for WDE V3 CLI integration tests.

```bash
wde init --root examples/v3-fixture --force
wde run static --root examples/v3-fixture
wde deliver-check --root examples/v3-fixture
wde report --root examples/v3-fixture
# fallbacks: python -m wde …  |  python wde.py …
```
