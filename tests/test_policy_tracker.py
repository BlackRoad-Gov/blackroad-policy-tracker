"""Tests for policy_tracker.py"""
import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import policy_tracker as pt
pt.DB_PATH = Path("/tmp/test_policy_tracker.db")


@pytest.fixture(autouse=True)
def clean_db():
    if pt.DB_PATH.exists():
        pt.DB_PATH.unlink()
    pt.init_db()
    yield
    if pt.DB_PATH.exists():
        pt.DB_PATH.unlink()


def make_policy(**kwargs):
    defaults = dict(
        title="Test Policy", number="POL-001", policy_type=pt.PolicyType.LAW,
        jurisdiction="Federal", summary="A test policy for unit testing."
    )
    defaults.update(kwargs)
    return pt.create_policy(**defaults)


def test_create_policy():
    policy = make_policy()
    assert policy.title == "Test Policy"
    assert policy.status == pt.PolicyStatus.DRAFT
    assert policy.policy_id is not None


def test_unique_policy_number():
    make_policy(number="POL-UNIQUE-1")
    with pytest.raises(Exception):
        make_policy(number="POL-UNIQUE-1", title="Duplicate")


def test_propose_amendment():
    policy = make_policy(number="POL-AMD-1")
    amendment = pt.propose_amendment(
        policy.policy_id, "Section 1", "Old text", "New text",
        "Correction", "2025-01-01"
    )
    assert amendment.policy_id == policy.policy_id
    assert amendment.status == "proposed"


def test_submit_comment():
    policy = make_policy(number="POL-CMT-1")
    comment = pt.submit_comment(
        policy.policy_id, "Jane Citizen", "Civil Society",
        "I support this policy.", pt.Sentiment.SUPPORT
    )
    assert comment.sentiment == pt.Sentiment.SUPPORT


def test_enact_policy():
    policy = make_policy(number="POL-ENACT-1")
    result = pt.enact_policy(policy.policy_id)
    assert result is True
    enacted = pt.get_policies_by_status(pt.PolicyStatus.ENACTED)
    assert any(p["policy_id"] == policy.policy_id for p in enacted)


def test_repeal_policy():
    policy = make_policy(number="POL-REP-1")
    pt.enact_policy(policy.policy_id)
    pt.repeal_policy(policy.policy_id)
    repealed = pt.get_policies_by_status(pt.PolicyStatus.REPEALED)
    assert any(p["policy_id"] == policy.policy_id for p in repealed)


def test_search_policies():
    make_policy(number="POL-SRCH-1", title="Environmental Regulation", summary="About the environment.")
    results = pt.search_policies("Environmental")
    assert len(results) >= 1


def test_get_timeline():
    policy = make_policy(number="POL-TML-1")
    pt.enact_policy(policy.policy_id)
    timeline = pt.get_timeline(policy.policy_id)
    assert len(timeline) >= 2
    types = [t["type"] for t in timeline]
    assert "status_change" in types


def test_export_report():
    policy = make_policy(number="POL-RPT-1", title="Data Privacy Law")
    pt.submit_comment(policy.policy_id, "Bob", "Tech Corp", "Good policy", pt.Sentiment.SUPPORT)
    report = pt.export_report(policy.policy_id)
    assert "POLICY REPORT" in report
    assert "Data Privacy Law" in report


def test_stats():
    make_policy(number="POL-STAT-1")
    make_policy(number="POL-STAT-2", policy_type=pt.PolicyType.REGULATION)
    stats = pt.policy_summary_stats()
    assert stats["total_policies"] >= 2
    assert "by_status" in stats
    assert "by_type" in stats
