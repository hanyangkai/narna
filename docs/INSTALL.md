# Install NARNA

## PyPI (recommended)

```bash
pip install narna
narna doctor
```

## From source

```bash
git clone https://github.com/hanyangkai/narna.git
cd narna
pip install -e .
narna doctor
```

## Hello governance (enforce mode)

```python
from narna import wrap

agent = wrap(my_langgraph_app, vap=True, mode="enforce")
agent.run("summarize quarterly report")
```

Set production default:

```bash
export NARNA_ADAPTER_MODE=enforce
```

## Cloud API

- Site: https://narna.org
- API: https://api.narna.org
- Health: `GET /v1/health`

## Publish (maintainers)

GitHub Action `.github/workflows/publish-pypi.yml` runs on tag `v*.*.*` with secret `PYPI_API_TOKEN`.
