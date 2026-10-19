"""Downstream league settings only. Never stores engine tokens or role grants."""
import re
import sqlite3
from contextlib import contextmanager


SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)


class Conflict(Exception):
    pass


class Store:
    def __init__(self, path):
        self.path = str(path)
        if self.path == ":memory:":
            raise ValueError("Use a file-backed database for persistent settings")
        with self.connection() as db:
            version=db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0,1):
                raise ValueError("Unsupported downstream schema version")
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY CHECK(version=1)
                );
                INSERT OR IGNORE INTO schema_version VALUES(1);
                CREATE TABLE IF NOT EXISTS leagues (
                    slug TEXT PRIMARY KEY,
                    organization_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1 CHECK(version>0),
                    synthetic INTEGER NOT NULL DEFAULT 0 CHECK(synthetic IN (0,1))
                );
            """)
            db.execute("PRAGMA user_version=1")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def add_league(self, slug, organization_id, name, timezone="UTC", *, synthetic=False):
        """Operator provisioning, never a public HTTP action or membership grant."""
        if not isinstance(slug, str) or len(slug)>63 or not SLUG.fullmatch(slug):
            raise ValueError("Invalid league slug")
        if not isinstance(organization_id, str) or not organization_id.strip() or len(organization_id)>128:
            raise ValueError("Invalid engine organization")
        name, timezone = validate_settings(name, timezone)
        with self.connection() as db:
            db.execute("INSERT INTO leagues(slug,organization_id,name,timezone,synthetic) VALUES(?,?,?,?,?)",
                       (slug, organization_id, name, timezone, int(synthetic)))

    def league(self, slug):
        with self.connection() as db:
            row = db.execute("SELECT * FROM leagues WHERE slug=?", (slug,)).fetchone()
            return dict(row) if row else None

    def update_settings(self, slug, organization_id, name, timezone, version):
        name, timezone = validate_settings(name, timezone)
        if type(version) is not int or version<1:
            raise ValueError("A positive settings version is required")
        with self.connection() as db:
            cursor = db.execute("UPDATE leagues SET name=?,timezone=?,version=version+1 "
                                "WHERE slug=? AND organization_id=? AND version=?",
                                (name, timezone, slug, organization_id, version))
            if cursor.rowcount != 1:
                raise Conflict("Settings changed; reload before retrying")
        return self.league(slug)

    def healthy(self):
        try:
            with self.connection() as db:
                return db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        except sqlite3.Error:
            return False


def validate_settings(name, timezone):
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    if not isinstance(name, str) or not 1<=len(name.strip())<=120 or any(ord(c)<32 for c in name):
        raise ValueError("League name must contain 1 to 120 printable characters")
    if not isinstance(timezone, str) or len(timezone)>64:
        raise ValueError("A valid IANA timezone is required")
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("A valid IANA timezone is required") from None
    return name.strip(), timezone
