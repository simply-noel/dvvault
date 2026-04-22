# DevVault

DevVault is my first real approach to building a Python package for pip.

It started as a personal tool I actually use to save commands, debugging fixes, small notes, and useful snippets without dumping them into random files or forgetting them later.

The goal is simple: keep a fast local CLI vault that is actually useful in real workflow, while also shaping it into something solid enough to package, maintain, and eventually push further as a more serious and possibly commercial tool.

## Why I built this

I wanted a local command-line tool that could help me store things like:

- terminal commands I reuse
- quick debugging fixes
- short notes
- tagged references
- things I normally forget and then have to rediscover

Instead of throwing that stuff into scattered text files, I wanted one clean place for all of it.

## What it does

DevVault lets you:

- add entries with a type and tags
- list and search entries
- select entries using combined filters
- pin important entries
- view recent entries
- edit and delete entries
- copy entry content to clipboard
- back up and restore the database
- reset the vault when needed
- view quick stats

## Install

For local development:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .