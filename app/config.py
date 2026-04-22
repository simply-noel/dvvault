from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"

DB_FILENAME = os.getenv("DEVVAULT_DB_FILENAME", "devvault.db")
BACKUP_FILENAME = os.getenv("DEVVAULT_BACKUP_FILENAME", "devvault_backup.db")

DB_PATH = DATA_DIR / DB_FILENAME
BACKUP_PATH = BACKUP_DIR / BACKUP_FILENAME

DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
