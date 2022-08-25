# jackal

## Requirement

- Poetry
- Python 3.9+

## Setup

`.env` ファイルを作成して, ログイン情報を記述する.

```txt
EMAIL=
PASSWORD=
```

## Usage

```bash
poetry install
poetry run python -m jackal <USER>

# Usage: python -m jackal [OPTIONS] USER [START_DATE] [END_DATE]

# Arguments:
#   USER          Username  [required]
#   [START_DATE]  [default: 20220607]
#   [END_DATE]    [default: 20220823]
```
