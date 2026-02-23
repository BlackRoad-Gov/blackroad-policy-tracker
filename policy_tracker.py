#!/usr/bin/env python3
"""
BlackRoad Policy Tracker — Government policy and legislation tracker
"""

import sqlite3
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from enum import Enum
from pathlib import Path


DB_PATH = Path("policy_tracker.db")


class PolicyType(str, Enum):
    LAW = "law"
    REGULATION = "regulation"
    ORDINANCE = "ordinance"
    EXECUTIVE_ORDER = "executive_order"


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    ENACTED = "enacted"
    AMENDED = "amended"
    REPEALED = "repealed"


class Sentiment(str, Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"


@dataclass
class Policy:
    title: str
    number: str
    policy_type: PolicyType
    jurisdiction: str
    summary: str
    full_text: str = ""
    status: PolicyStatus = PolicyStatus.DRAFT
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Amendment:
    policy_id: str
    section: str
    old_text: str
    new_text: str
    reason: str
    effective_date: str
    amendment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "proposed"


@dataclass
class Comment:
    policy_id: str
    commenter: str
    organization: str
    content: str
    sentiment: Sentiment
    comment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    submitted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the database with FTS5 support."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS policies (
            policy_id       TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            number          TEXT UNIQUE NOT NULL,
            policy_type     TEXT NOT NULL,
            status          TEXT DEFAULT 'draft',
            jurisdiction    TEXT NOT NULL,
            summary         TEXT NOT NULL,
            full_text       TEXT DEFAULT '',
            effective_date  TEXT,
            expiry_date     TEXT,
            tags            TEXT DEFAULT '[]',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS policies_fts USING fts5(
            policy_id UNINDEXED,
            title,
            number,
            summary,
            full_text,
            tags,
            content='policies',
            content_rowid='rowid'
        );

        CREATE TABLE IF NOT EXISTS amendments (
            amendment_id    TEXT PRIMARY KEY,
            policy_id       TEXT NOT NULL,
            section         TEXT NOT NULL,
            old_text        TEXT NOT NULL,
            new_text        TEXT NOT NULL,
            reason          TEXT NOT NULL,
            effective_date  TEXT NOT NULL,
            proposed_at     TEXT NOT NULL,
            status          TEXT DEFAULT 'proposed',
            FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            comment_id      TEXT PRIMARY KEY,
            policy_id       TEXT NOT NULL,
            commenter       TEXT NOT NULL,
            organization    TEXT NOT NULL,
            content         TEXT NOT NULL,
            sentiment       TEXT NOT NULL,
            submitted_at    TEXT NOT NULL,
            FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
        );

        CREATE TABLE IF NOT EXISTS status_history (
            history_id      TEXT PRIMARY KEY,
            policy_id       TEXT NOT NULL,
            old_status      TEXT,
            new_status      TEXT NOT NULL,
            changed_at      TEXT NOT NULL,
            changed_by      TEXT DEFAULT 'system',
            FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
        );

        CREATE TRIGGER IF NOT EXISTS policies_ai AFTER INSERT ON policies BEGIN
            INSERT INTO policies_fts(policy_id, title, number, summary, full_text, tags)
            VALUES (new.policy_id, new.title, new.number, new.summary, new.full_text, new.tags);
        END;

        CREATE TRIGGER IF NOT EXISTS policies_au AFTER UPDATE ON policies BEGIN
            UPDATE policies_fts SET title=new.title, summary=new.summary,
                full_text=new.full_text, tags=new.tags
            WHERE policy_id=new.policy_id;
        END;
    """)
    conn.commit()
    conn.close()


def _record_status_change(policy_id: str, old_status: Optional[str], new_status: str, changed_by: str = "system"):
    conn = get_connection()
    conn.execute(
        "INSERT INTO status_history VALUES (?,?,?,?,?,?)",
        (str(uuid.uuid4()), policy_id, old_status, new_status, datetime.utcnow().isoformat(), changed_by)
    )
    conn.commit()
    conn.close()


def create_policy(title: str, number: str, policy_type: PolicyType, jurisdiction: str,
                  summary: str, full_text: str = "", effective_date: Optional[str] = None,
                  expiry_date: Optional[str] = None, tags: Optional[List[str]] = None) -> Policy:
    """Create a new policy."""
    init_db()
    policy = Policy(
        title=title, number=number, policy_type=policy_type,
        jurisdiction=jurisdiction, summary=summary, full_text=full_text,
        effective_date=effective_date, expiry_date=expiry_date,
        tags=tags or []
    )
    conn = get_connection()
    conn.execute(
        "INSERT INTO policies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (policy.policy_id, title, number, policy_type.value if isinstance(policy_type, PolicyType) else policy_type,
         policy.status.value, jurisdiction, summary, full_text,
         effective_date, expiry_date, json.dumps(tags or []),
         policy.created_at, policy.updated_at)
    )
    conn.commit()
    conn.close()
    _record_status_change(policy.policy_id, None, policy.status.value)
    return policy


def propose_amendment(policy_id: str, section: str, old_text: str, new_text: str,
                      reason: str, effective_date: str) -> Amendment:
    """Propose an amendment to an existing policy."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM policies WHERE policy_id=?", (policy_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Policy {policy_id} not found")
    amendment = Amendment(
        policy_id=policy_id, section=section, old_text=old_text,
        new_text=new_text, reason=reason, effective_date=effective_date
    )
    conn.execute(
        "INSERT INTO amendments VALUES (?,?,?,?,?,?,?,?,?)",
        (amendment.amendment_id, policy_id, section, old_text, new_text,
         reason, effective_date, amendment.proposed_at, amendment.status)
    )
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE policies SET status=?, updated_at=? WHERE policy_id=?",
        (PolicyStatus.AMENDED.value, now, policy_id)
    )
    conn.commit()
    conn.close()
    return amendment


def submit_comment(policy_id: str, commenter: str, organization: str,
                   content: str, sentiment: Sentiment) -> Comment:
    """Submit a public comment on a policy."""
    conn = get_connection()
    row = conn.execute("SELECT policy_id FROM policies WHERE policy_id=?", (policy_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Policy {policy_id} not found")
    comment = Comment(
        policy_id=policy_id, commenter=commenter, organization=organization,
        content=content, sentiment=sentiment
    )
    conn.execute(
        "INSERT INTO comments VALUES (?,?,?,?,?,?,?)",
        (comment.comment_id, policy_id, commenter, organization,
         content, sentiment.value if isinstance(sentiment, Sentiment) else sentiment,
         comment.submitted_at)
    )
    conn.commit()
    conn.close()
    return comment


def enact_policy(policy_id: str, effective_date: Optional[str] = None) -> bool:
    """Enact a proposed policy."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM policies WHERE policy_id=?", (policy_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Policy {policy_id} not found")
    now = datetime.utcnow().isoformat()
    eff = effective_date or now
    old_status = row["status"]
    conn.execute(
        "UPDATE policies SET status=?, effective_date=?, updated_at=? WHERE policy_id=?",
        (PolicyStatus.ENACTED.value, eff, now, policy_id)
    )
    conn.commit()
    conn.close()
    _record_status_change(policy_id, old_status, PolicyStatus.ENACTED.value)
    return True


def repeal_policy(policy_id: str) -> bool:
    """Repeal an enacted policy."""
    conn = get_connection()
    row = conn.execute("SELECT status FROM policies WHERE policy_id=?", (policy_id,)).fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Policy {policy_id} not found")
    old_status = row["status"]
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE policies SET status=?, updated_at=? WHERE policy_id=?",
        (PolicyStatus.REPEALED.value, now, policy_id)
    )
    conn.commit()
    conn.close()
    _record_status_change(policy_id, old_status, PolicyStatus.REPEALED.value)
    return True


def search_policies(query: str) -> List[dict]:
    """Full-text search across policies."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT p.* FROM policies p
               JOIN policies_fts fts ON p.policy_id = fts.policy_id
               WHERE policies_fts MATCH ?
               ORDER BY rank""",
            (query,)
        ).fetchall()
    except Exception:
        rows = conn.execute(
            "SELECT * FROM policies WHERE title LIKE ? OR summary LIKE ? OR number LIKE ?",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["tags"] = json.loads(d.get("tags", "[]"))
        result.append(d)
    return result


def get_timeline(policy_id: str) -> List[dict]:
    """Get the full timeline of a policy's status changes."""
    conn = get_connection()
    history = conn.execute(
        "SELECT * FROM status_history WHERE policy_id=? ORDER BY changed_at ASC",
        (policy_id,)
    ).fetchall()
    amendments = conn.execute(
        "SELECT * FROM amendments WHERE policy_id=? ORDER BY proposed_at ASC",
        (policy_id,)
    ).fetchall()
    conn.close()

    timeline = []
    for h in history:
        timeline.append({
            "type": "status_change",
            "date": h["changed_at"],
            "old_status": h["old_status"],
            "new_status": h["new_status"],
            "changed_by": h["changed_by"]
        })
    for a in amendments:
        timeline.append({
            "type": "amendment",
            "date": a["proposed_at"],
            "section": a["section"],
            "reason": a["reason"],
            "effective_date": a["effective_date"],
            "status": a["status"]
        })
    timeline.sort(key=lambda x: x["date"])
    return timeline


def export_report(policy_id: str) -> str:
    """Export a comprehensive policy report."""
    conn = get_connection()
    policy = conn.execute("SELECT * FROM policies WHERE policy_id=?", (policy_id,)).fetchone()
    if not policy:
        conn.close()
        raise ValueError(f"Policy {policy_id} not found")
    amendments = conn.execute(
        "SELECT * FROM amendments WHERE policy_id=? ORDER BY proposed_at",
        (policy_id,)
    ).fetchall()
    comments = conn.execute(
        "SELECT * FROM comments WHERE policy_id=? ORDER BY submitted_at",
        (policy_id,)
    ).fetchall()
    conn.close()

    sentiment_counts = {"support": 0, "oppose": 0, "neutral": 0}
    for c in comments:
        sentiment_counts[c["sentiment"]] = sentiment_counts.get(c["sentiment"], 0) + 1

    tags = json.loads(policy["tags"])
    lines = [
        "=" * 70,
        "POLICY REPORT",
        "=" * 70,
        f"Policy Number : {policy['number']}",
        f"Title         : {policy['title']}",
        f"Type          : {policy['policy_type'].upper()}",
        f"Status        : {policy['status'].upper()}",
        f"Jurisdiction  : {policy['jurisdiction']}",
        f"Created       : {policy['created_at'][:10]}",
        f"Effective     : {policy['effective_date'] or 'TBD'}",
        f"Expiry        : {policy['expiry_date'] or 'N/A'}",
        f"Tags          : {', '.join(tags)}",
        "",
        "SUMMARY",
        "-" * 40,
        policy["summary"],
        "",
        f"AMENDMENTS ({len(amendments)})",
        "-" * 40,
    ]
    for a in amendments:
        lines.append(f"  Section: {a['section']} | Effective: {a['effective_date']}")
        lines.append(f"  Reason: {a['reason']}")
        lines.append("")

    lines += [
        f"PUBLIC COMMENTS ({len(comments)})",
        "-" * 40,
        f"  Support: {sentiment_counts['support']}",
        f"  Oppose : {sentiment_counts['oppose']}",
        f"  Neutral: {sentiment_counts['neutral']}",
        "",
    ]
    for c in comments[:5]:
        lines.append(f"  [{c['sentiment'].upper()}] {c['commenter']} ({c['organization']})")
        lines.append(f"  {c['content'][:120]}...")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def get_policies_by_status(status: PolicyStatus) -> List[dict]:
    """Get all policies with a specific status."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM policies WHERE status=? ORDER BY created_at DESC",
        (status.value,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["tags"] = json.loads(d.get("tags", "[]"))
        result.append(d)
    return result


def policy_summary_stats() -> dict:
    """Get summary statistics for all policies."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
    by_status = {}
    for s in PolicyStatus:
        cnt = conn.execute("SELECT COUNT(*) FROM policies WHERE status=?", (s.value,)).fetchone()[0]
        by_status[s.value] = cnt
    by_type = {}
    for t in PolicyType:
        cnt = conn.execute("SELECT COUNT(*) FROM policies WHERE policy_type=?", (t.value,)).fetchone()[0]
        by_type[t.value] = cnt
    total_amendments = conn.execute("SELECT COUNT(*) FROM amendments").fetchone()[0]
    total_comments = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
    by_sentiment = {}
    for s in Sentiment:
        cnt = conn.execute("SELECT COUNT(*) FROM comments WHERE sentiment=?", (s.value,)).fetchone()[0]
        by_sentiment[s.value] = cnt
    conn.close()
    return {
        "total_policies": total,
        "by_status": by_status,
        "by_type": by_type,
        "total_amendments": total_amendments,
        "total_comments": total_comments,
        "comment_sentiment": by_sentiment,
    }


def cli():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python policy_tracker.py <command>")
        print("Commands: create, search, stats, enact, repeal, comment, report, timeline")
        return
    init_db()
    cmd = sys.argv[1]
    if cmd == "stats":
        import json
        print(json.dumps(policy_summary_stats(), indent=2))
    elif cmd == "search" and len(sys.argv) >= 3:
        results = search_policies(sys.argv[2])
        for r in results:
            print(f"[{r['status'].upper()}] {r['number']} — {r['title']}")
    elif cmd == "list":
        conn = get_connection()
        rows = conn.execute("SELECT * FROM policies ORDER BY created_at DESC").fetchall()
        conn.close()
        for r in rows:
            print(f"[{r['status'].upper()}] {r['number']} — {r['title']}")
    elif cmd == "report" and len(sys.argv) >= 3:
        print(export_report(sys.argv[2]))
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    cli()
