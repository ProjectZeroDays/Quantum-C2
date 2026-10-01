"""Tests for quantum.social.messaging — messaging & social engineering."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from quantum.social.messaging import (
    messaging_dashboard_state,
    list_messaging_platforms,
    list_social_engineering_techniques,
    list_voice_clone_providers,
    list_face_clone_providers,
    generate_social_engineering_campaign,
)


class TestMessagingDashboardState:
    def test_returns_dict(self):
        result = messaging_dashboard_state()
        assert isinstance(result, dict)

    def test_has_platforms(self):
        result = messaging_dashboard_state()
        assert "platforms" in result
        assert isinstance(result["platforms"], dict)


class TestListMessagingPlatforms:
    def test_returns_dict(self):
        result = list_messaging_platforms()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_messaging_platforms()
        assert len(result) > 0

    def test_entries_have_name(self):
        result = list_messaging_platforms()
        for key, p in result.items():
            assert "name" in p

    def test_known_platforms_present(self):
        result = list_messaging_platforms()
        names = [p["name"].lower() for p in result.values()]
        assert any("whatsapp" in n for n in names)
        assert any("telegram" in n for n in names)


class TestListSocialEngineeringTechniques:
    def test_returns_dict(self):
        result = list_social_engineering_techniques()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_social_engineering_techniques()
        assert len(result) > 0

    def test_known_techniques_present(self):
        result = list_social_engineering_techniques()
        names = [t["name"].lower() for t in result.values()]
        assert any("phishing" in n for n in names)


class TestListVoiceCloneProviders:
    def test_returns_dict(self):
        result = list_voice_clone_providers()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_voice_clone_providers()
        assert len(result) > 0


class TestListFaceCloneProviders:
    def test_returns_dict(self):
        result = list_face_clone_providers()
        assert isinstance(result, dict)

    def test_non_empty(self):
        result = list_face_clone_providers()
        assert len(result) > 0


class TestGenerateSocialEngineeringCampaign:
    def test_returns_dict(self):
        result = generate_social_engineering_campaign("whatsapp", "phishing", "target@example.com")
        assert isinstance(result, dict)

    def test_has_platform_field(self):
        result = generate_social_engineering_campaign("whatsapp", "phishing", "target@example.com")
        assert result["platform"] == "whatsapp"

    def test_has_technique(self):
        result = generate_social_engineering_campaign("whatsapp", "phishing", "target@example.com")
        assert result["technique"] == "phishing"

    def test_invalid_platform_returns_error(self):
        result = generate_social_engineering_campaign("invalid_platform", "phishing", "target@example.com")
        assert isinstance(result, dict)
        assert "error" in result
