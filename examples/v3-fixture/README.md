# V3 fixture frontend

Minimal static board layout for WDE V3 CLI integration tests.

```bash
python -m wde.cli.main init --root examples/v3-fixture --force
python -m wde.cli.main run static --root examples/v3-fixture
python -m wde.cli.main deliver-check --root examples/v3-fixture
python -m wde.cli.main report --root examples/v3-fixture
```
