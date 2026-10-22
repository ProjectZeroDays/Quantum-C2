#!/usr/bin/env python3
"""Tests for MessagingRCEAgent agent."""
import pytest


from MessagingRCE.messagingrceagent import MessagingRCEAgent


def test_describe():
    agent = MessagingRCEAgent()
    result = agent.describe()
    assert result["name"] == "messagingrceagent"
    assert "description" in result
    assert result["category"] == "red_teaming"


def test_capabilities():
    agent = MessagingRCEAgent()
    desc = agent.describe()
    assert "capabilities" in desc
    assert len(desc["capabilities"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
