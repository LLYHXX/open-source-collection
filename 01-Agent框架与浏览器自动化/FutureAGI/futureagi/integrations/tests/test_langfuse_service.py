"""Unit tests for LangfuseService (all HTTP calls mocked)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from integrations.services.langfuse_service import LangfuseService

HOST = "https://langfuse.example.com"
CREDS = {"public_key": "pk-lf-test", "secret_key": "sk-lf-test"}


@pytest.fixture
def service():
    return LangfuseService()


def _mock_response(status_code=200, json_data=None, raise_for_status=None):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    if raise_for_status:
        resp.raise_for_status.side_effect = raise_for_status
    else:
        resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# validate_credentials
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLangfuseServiceValidateCredentials:
    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_success(self, mock_req, service):
        projects_resp = _mock_response(
            200,
            {"data": [{"id": "p1", "name": "proj-1"}]},
        )
        traces_resp = _mock_response(200, {"meta": {"totalItems": 42}})
        mock_req.side_effect = [projects_resp, traces_resp]

        result = service.validate_credentials(HOST, CREDS)

        assert result["valid"] is True
        assert len(result["projects"]) == 1
        assert result["projects"][0]["name"] == "proj-1"
        assert result["total_traces"] == 42

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_401_returns_invalid(self, mock_req, service):
        mock_req.return_value = _mock_response(401)

        result = service.validate_credentials(HOST, CREDS)

        assert result["valid"] is False
        assert "Invalid credentials" in result["error"]

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_non_200_returns_invalid(self, mock_req, service):
        mock_req.return_value = _mock_response(500)

        result = service.validate_credentials(HOST, CREDS)

        assert result["valid"] is False
        assert "Unexpected response" in result["error"]
        assert "500" in result["error"]

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_connection_error(self, mock_req, service):
        mock_req.side_effect = requests.exceptions.ConnectionError("refused")

        result = service.validate_credentials(HOST, CREDS)

        assert result["valid"] is False
        assert "Could not reach" in result["error"]

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_timeout(self, mock_req, service):
        mock_req.side_effect = requests.exceptions.Timeout("timed out")

        result = service.validate_credentials(HOST, CREDS)

        assert result["valid"] is False
        assert "timed out" in result["error"]

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_unexpected_exception(self, mock_req, service):
        mock_req.side_effect = RuntimeError("boom")

        result = service.validate_credentials(HOST, CREDS)

        assert result["valid"] is False
        assert "Validation failed" in result["error"]

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_traces_count_failure_graceful(self, mock_req, service):
        """If trace count endpoint fails, total_traces defaults to 0."""
        projects_resp = _mock_response(200, {"data": [{"id": "p1", "name": "proj-1"}]})
        mock_req.side_effect = [projects_resp, Exception("traces fail")]

        result = service.validate_credentials(HOST, CREDS)

        assert result["valid"] is True
        assert result["total_traces"] == 0

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_uses_basic_auth(self, mock_req, service):
        mock_req.return_value = _mock_response(200, {"data": []})

        service.validate_credentials(HOST, CREDS)

        call_kwargs = mock_req.call_args_list[0]
        assert call_kwargs.kwargs["auth"] == ("pk-lf-test", "sk-lf-test")

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_ca_certificate_passes_verify(self, mock_req, service):
        """When ca_certificate is provided, a temp file path is used for verify."""
        projects_resp = _mock_response(200, {"data": []})
        traces_resp = _mock_response(200, {"meta": {"totalItems": 0}})
        mock_req.side_effect = [projects_resp, traces_resp]

        service.validate_credentials(
            HOST, CREDS, ca_certificate="-----BEGIN CERT-----\ntest\n-----END CERT-----"
        )

        # First call should have verify= set to a temp file path (string, not True)
        first_call = mock_req.call_args_list[0]
        assert isinstance(first_call.kwargs["verify"], str)
        assert first_call.kwargs["verify"].endswith(".pem")

    @patch("integrations.services.langfuse_service.requests.request")
    def test_validate_empty_projects_list(self, mock_req, service):
        """Validation succeeds with an empty project list."""
        projects_resp = _mock_response(200, {"data": []})
        traces_resp = _mock_response(200, {"meta": {"totalItems": 0}})
        mock_req.side_effect = [projects_resp, traces_resp]

        result = service.validate_credentials(HOST, CREDS)

        assert result["valid"] is True
        assert result["projects"] == []
        assert result["total_traces"] == 0


# ---------------------------------------------------------------------------
# fetch_traces
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLangfuseServiceFetchTraces:
    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_traces_success(self, mock_req, service):
        mock_req.return_value = _mock_response(
            200,
            {
                "data": [{"id": "t1"}, {"id": "t2"}],
                "meta": {"totalItems": 50, "totalPages": 5, "page": 1},
            },
        )

        result = service.fetch_traces(HOST, CREDS)

        assert len(result["traces"]) == 2
        assert result["total_items"] == 50
        assert result["has_more"] is True
        assert result["next_page"] == 2

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_traces_with_timestamps(self, mock_req, service):
        mock_req.return_value = _mock_response(
            200, {"data": [], "meta": {"totalItems": 0, "totalPages": 1, "page": 1}}
        )

        service.fetch_traces(
            HOST,
            CREDS,
            from_timestamp="2024-01-01T00:00:00Z",
            to_timestamp="2024-01-02T00:00:00Z",
        )

        params = mock_req.call_args.kwargs["params"]
        assert params["fromTimestamp"] == "2024-01-01T00:00:00Z"
        assert params["toTimestamp"] == "2024-01-02T00:00:00Z"

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_traces_http_error_raises(self, mock_req, service):
        http_err = requests.exceptions.HTTPError(response=_mock_response(500))
        mock_req.return_value = _mock_response(500, raise_for_status=http_err)

        with pytest.raises(requests.exceptions.HTTPError):
            service.fetch_traces(HOST, CREDS)

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_traces_last_page(self, mock_req, service):
        mock_req.return_value = _mock_response(
            200,
            {
                "data": [{"id": "t1"}],
                "meta": {"totalItems": 5, "totalPages": 1, "page": 1},
            },
        )

        result = service.fetch_traces(HOST, CREDS)

        assert result["has_more"] is False

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_traces_pagination_params(self, mock_req, service):
        mock_req.return_value = _mock_response(
            200, {"data": [], "meta": {"totalItems": 0, "totalPages": 1, "page": 3}}
        )

        service.fetch_traces(HOST, CREDS, page=3, limit=50)

        params = mock_req.call_args.kwargs["params"]
        assert params["page"] == 3
        assert params["limit"] == 50

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_traces_empty_data(self, mock_req, service):
        """No traces returned → empty traces list."""
        mock_req.return_value = _mock_response(
            200, {"data": [], "meta": {"totalItems": 0, "totalPages": 1, "page": 1}}
        )

        result = service.fetch_traces(HOST, CREDS)

        assert result["traces"] == []
        assert result["total_items"] == 0
        assert result["has_more"] is False

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_traces_middle_page_has_more(self, mock_req, service):
        """Page 2 of 5 → has_more is True."""
        mock_req.return_value = _mock_response(
            200,
            {
                "data": [{"id": "t1"}],
                "meta": {"totalItems": 100, "totalPages": 5, "page": 2},
            },
        )

        result = service.fetch_traces(HOST, CREDS, page=2)

        assert result["has_more"] is True
        assert result["next_page"] == 3

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_traces_missing_meta(self, mock_req, service):
        """Response with no meta key → safe defaults."""
        mock_req.return_value = _mock_response(200, {"data": [{"id": "t1"}]})

        result = service.fetch_traces(HOST, CREDS)

        assert result["traces"] == [{"id": "t1"}]
        assert result["total_items"] == 0
        assert result["has_more"] is False


# ---------------------------------------------------------------------------
# fetch_trace_detail
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLangfuseServiceFetchTraceDetail:
    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_detail_success(self, mock_req, service):
        trace_data = {"id": "t1", "name": "test", "observations": []}
        mock_req.return_value = _mock_response(200, trace_data)

        result = service.fetch_trace_detail(HOST, CREDS, "t1")

        assert result["id"] == "t1"

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_detail_404_raises(self, mock_req, service):
        http_err = requests.exceptions.HTTPError(response=_mock_response(404))
        mock_req.return_value = _mock_response(404, raise_for_status=http_err)

        with pytest.raises(requests.exceptions.HTTPError):
            service.fetch_trace_detail(HOST, CREDS, "missing")

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_detail_429_raises(self, mock_req, service):
        http_err = requests.exceptions.HTTPError(response=_mock_response(429))
        mock_req.return_value = _mock_response(429, raise_for_status=http_err)

        with pytest.raises(requests.exceptions.HTTPError):
            service.fetch_trace_detail(HOST, CREDS, "t1")

    @patch("integrations.services.langfuse_service.requests.request")
    def test_fetch_detail_url_construction(self, mock_req, service):
        mock_req.return_value = _mock_response(200, {"id": "abc"})

        service.fetch_trace_detail(HOST, CREDS, "abc")

        url = mock_req.call_args.kwargs["url"]
        assert url == "https://langfuse.example.com/api/public/traces/abc"
