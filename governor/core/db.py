"""
core/db.py — SQLite 操作層
設計原則：records 表一旦寫入即不可修改（immutable），防止幻覺污染。
"""

import aiosqlite
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "/data/governor.db")

SCHEMA = """
-- 工作階段
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    topic       TEXT NOT NULL,
    stakeholders TEXT,           -- JSON array string
    status      TEXT DEFAULT 'active',  -- active | closed
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- 原始輸入記錄（寫入後嚴禁修改）
CREATE TABLE IF NOT EXISTS records (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    role         TEXT NOT NULL,  -- user | stakeholder | pm | engineer | system
    stage        TEXT NOT NULL,  -- interview | hypothesis | gitnexus_audit | tradeoff | conclusion | memo
    content      TEXT NOT NULL,  -- 原始文字，嚴禁修改
    sha256_hash  TEXT NOT NULL,  -- 防竄改憑據
    source_note  TEXT,           -- 選填：說明來源情境
    created_at   TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Stage 01/02/03 進度
CREATE TABLE IF NOT EXISTS stage_progress (
    id           TEXT PRIMARY KEY,
    session_id   TEXT NOT NULL,
    stage        TEXT NOT NULL,  -- 01 | 02 | 03
    status       TEXT DEFAULT 'pending',  -- pending | in_progress | passed | blocked
    gate_result  TEXT,           -- JSON: 詳細通過/阻斷結果
    completed_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Reminder 記錄
CREATE TABLE IF NOT EXISTS reminders (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    reminder_type   TEXT NOT NULL,  -- unrecorded_stage | long_idle | missing_field
    message         TEXT NOT NULL,
    triggered_at    TEXT NOT NULL,
    acknowledged_at TEXT,           -- NULL = 尚未確認
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- 生成報告 metadata
CREATE TABLE IF NOT EXISTS reports (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    report_type     TEXT NOT NULL,  -- memo | trace | full
    file_path       TEXT NOT NULL,
    unfilled_fields TEXT,           -- JSON array: 哪些欄位是 【⏳ 待確認】
    generated_at    TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
"""


async def init_db() -> None:
    """初始化資料庫，建立所有資料表。"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Sessions ───────────────────────────────────────────────────────────────

async def create_session(session_id: str, topic: str, stakeholders: list[str] | None = None) -> dict:
    import json
    ts = now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO sessions (id, topic, stakeholders, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (session_id, topic, json.dumps(stakeholders or []), "active", ts, ts)
        )
        await db.commit()
    return {"id": session_id, "topic": topic, "stakeholders": stakeholders or [], "status": "active", "created_at": ts}


async def get_session(session_id: str) -> dict | None:
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            d = dict(row)
            d["stakeholders"] = json.loads(d["stakeholders"] or "[]")
            return d


async def list_sessions() -> list[dict]:
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM sessions ORDER BY created_at DESC") as cur:
            rows = await cur.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["stakeholders"] = json.loads(d["stakeholders"] or "[]")
                result.append(d)
            return result


async def close_session(session_id: str) -> bool:
    ts = now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE sessions SET status='closed', updated_at=? WHERE id=?", (ts, session_id)
        )
        await db.commit()
        return True


# ─── Records ────────────────────────────────────────────────────────────────

async def insert_record(record_id: str, session_id: str, role: str, stage: str,
                         content: str, sha256_hash: str, source_note: str | None = None) -> dict:
    ts = now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO records (id, session_id, role, stage, content, sha256_hash, source_note, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (record_id, session_id, role, stage, content, sha256_hash, source_note, ts)
        )
        await db.commit()
    return {
        "id": record_id, "session_id": session_id, "role": role,
        "stage": stage, "sha256_hash": sha256_hash,
        "source_note": source_note, "created_at": ts
    }


async def get_records(session_id: str, stage: str | None = None, role: str | None = None) -> list[dict]:
    query = "SELECT * FROM records WHERE session_id=?"
    params: list = [session_id]
    if stage:
        query += " AND stage=?"; params.append(stage)
    if role:
        query += " AND role=?"; params.append(role)
    query += " ORDER BY created_at ASC"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_last_record_time(session_id: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT created_at FROM records WHERE session_id=? ORDER BY created_at DESC LIMIT 1",
            (session_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else None


# ─── Stage Progress ──────────────────────────────────────────────────────────

async def upsert_stage_progress(progress_id: str, session_id: str, stage: str,
                                  status: str, gate_result: dict | None = None) -> dict:
    import json
    ts = now_iso()
    gate_json = json.dumps(gate_result) if gate_result else None
    completed = ts if status in ("passed", "blocked") else None
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO stage_progress (id, session_id, stage, status, gate_result, completed_at)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET status=excluded.status,
                gate_result=excluded.gate_result, completed_at=excluded.completed_at
        """, (progress_id, session_id, stage, status, gate_json, completed))
        await db.commit()
    return {"id": progress_id, "session_id": session_id, "stage": stage,
            "status": status, "gate_result": gate_result, "completed_at": completed}


async def get_stage_progress(session_id: str) -> list[dict]:
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM stage_progress WHERE session_id=? ORDER BY stage ASC", (session_id,)
        ) as cur:
            rows = await cur.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                if d["gate_result"]:
                    d["gate_result"] = json.loads(d["gate_result"])
                result.append(d)
            return result


# ─── Reminders ──────────────────────────────────────────────────────────────

async def insert_reminder(reminder_id: str, session_id: str, reminder_type: str, message: str) -> dict:
    ts = now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO reminders (id, session_id, reminder_type, message, triggered_at) VALUES (?,?,?,?,?)",
            (reminder_id, session_id, reminder_type, message, ts)
        )
        await db.commit()
    return {"id": reminder_id, "type": reminder_type, "message": message, "triggered_at": ts}


async def get_pending_reminders(session_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reminders WHERE session_id=? AND acknowledged_at IS NULL ORDER BY triggered_at DESC",
            (session_id,)
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def acknowledge_reminders(session_id: str) -> int:
    ts = now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "UPDATE reminders SET acknowledged_at=? WHERE session_id=? AND acknowledged_at IS NULL",
            (ts, session_id)
        )
        await db.commit()
        return cur.rowcount


# ─── Reports ────────────────────────────────────────────────────────────────

async def insert_report(report_id: str, session_id: str, report_type: str,
                          file_path: str, unfilled_fields: list[str]) -> dict:
    import json
    ts = now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reports (id, session_id, report_type, file_path, unfilled_fields, generated_at) VALUES (?,?,?,?,?,?)",
            (report_id, session_id, report_type, file_path, json.dumps(unfilled_fields), ts)
        )
        await db.commit()
    return {"id": report_id, "session_id": session_id, "report_type": report_type,
            "file_path": file_path, "unfilled_fields": unfilled_fields, "generated_at": ts}


async def list_reports(session_id: str | None = None) -> list[dict]:
    import json
    query = "SELECT * FROM reports"
    params = []
    if session_id:
        query += " WHERE session_id=?"
        params.append(session_id)
    query += " ORDER BY generated_at DESC"
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["unfilled_fields"] = json.loads(d["unfilled_fields"] or "[]")
                result.append(d)
            return result
