# DevVault

DevVault is a local CLI vault for commands, snippets, fixes, and notes.

It is designed for developers who keep reusing the same commands, debugging fixes, setup notes, and tiny knowledge fragments, then forget where they put them because apparently human memory ships without indexing.

## Features

- Add entries with a type and tags
- Normalize tags automatically
- List, search, and select with combined filters
- Show recent entries
- Pin important entries
- Copy entry content to clipboard
- Delete specific entries or clear filtered groups
- Backup, restore, and reset the database
- Show vault statistics
- Run tests against a separate test database

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
