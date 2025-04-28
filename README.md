## Installation

### Requirements

- We recommend using [uv](https://docs.astral.sh/uv/) to manage your Python projects. 

### Prerequisites

- Create virtual environment
```bash
uv venv
.venv\Scripts\activate
```

- Install packages
```bash
uv pip install -r requirements.txt
```

Run MCP Server:
```bash
uv run server.py
```

Run MCP Client:
```bash
uv run -- client.py http://localhost:8000/sse https://en.wikipedia.org/wiki/Red-chested_cuckoo
```
