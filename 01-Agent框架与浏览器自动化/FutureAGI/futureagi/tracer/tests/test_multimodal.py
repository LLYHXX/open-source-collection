"""
Tests for user and session info extraction utilities.
"""

from tracer.utils.multimodal import extract_user_session_info


class TestUserSessionInfoExtraction:
    """Test extracting user and session info from attributes."""

    def test_extract_user_id(self):
        attributes = {"user.id": "user123"}
        info = extract_user_session_info(attributes)
        assert info["user_id"] == "user123"

    def test_extract_session_id(self):
        attributes = {"session.id": "session456"}
        info = extract_user_session_info(attributes)
        assert info["session_id"] == "session456"

    def test_extract_user_attributes(self):
        attributes = {
            "user.email": "test@example.com",
            "user.name": "Test User",
        }
        info = extract_user_session_info(attributes)
        assert info["user_attributes"]["email"] == "test@example.com"
        assert info["user_attributes"]["name"] == "Test User"

    def test_extract_enduser_attributes(self):
        """Test alternate attribute names (enduser prefix)."""
        attributes = {
            "enduser.email": "enduser@example.com",
            "enduser.name": "End User",
        }
        info = extract_user_session_info(attributes)
        assert info["user_attributes"]["email"] == "enduser@example.com"
        assert info["user_attributes"]["name"] == "End User"

    def test_extract_empty_attributes(self):
        info = extract_user_session_info({})
        assert info["user_id"] is None
        assert info["session_id"] is None
