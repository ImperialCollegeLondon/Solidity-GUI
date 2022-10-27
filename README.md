# Solidity GUI

## Development

Setup your environment by installing dependencies from `requirements.txt`.

Then run the GUI with:

```python
python -m solidity-gui
```

### Dependencies

Dependencies are managed using the [pip-tools] tool chain.

Unpinned dependencies are specified in `pyproject.toml`. Pinned versions are
then produced with:

`pip-compile pyproject.toml`

To add/remove packages edit `pyproject.toml` and run the above command. To
upgrade all existing dependencies run:

`pip-compile --upgrade pyproject.toml`

[pip-tools]: https://github.com/jazzband/pip-tools
