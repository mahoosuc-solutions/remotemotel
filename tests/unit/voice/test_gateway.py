"""
Tests for Voice Gateway - Twilio webhook handling and signature validation
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import Request
from twilio.request_validator import RequestValidator

from packages.voice.gateway import VoiceGateway
from packages.voice.session import SessionManager


class TestTwilioSignatureValidation:
    """Test Twilio request signature validation"""

    @pytest.fixture
    def mock_session_manager(self):
        """Create mock session manager"""
        manager = Mock(spec=SessionManager)
        manager.create_session = AsyncMock()
        manager.get_active_sessions = AsyncMock(return_value=[])
        return manager

    @pytest.fixture
    def gateway_with_auth(self, mock_session_manager):
        """Create gateway with Twilio auth configured"""
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': 'ACtest123',
            'TWILIO_AUTH_TOKEN': 'test_auth_token',
            'TWILIO_PHONE_NUMBER': '+15551234567'
        }):
            return VoiceGateway(session_manager=mock_session_manager)

    @pytest.mark.asyncio
    async def test_signature_validation_with_https_forwarded_proto(self, gateway_with_auth):
        """
        Test signature validation with X-Forwarded-Proto header (Cloud Run scenario)

        This test simulates Cloud Run environment where:
        - External request is HTTPS
        - Cloud Run terminates SSL and forwards HTTP internally
        - X-Forwarded-Proto header indicates original scheme was HTTPS
        - Twilio signs the request with the HTTPS URL

        This test SHOULD FAIL initially because the code uses the internal HTTP URL
        instead of reconstructing the HTTPS URL from the X-Forwarded-Proto header.
        """
        # Create mock request
        mock_request = Mock(spec=Request)

        # Simulate Cloud Run: internal URL is HTTP, but external is HTTPS
        mock_request.url = "http://westbethel-operator-jvm6akkheq-uc.a.run.app/voice/twilio/inbound"
        mock_request.headers = {
            "X-Forwarded-Proto": "https",  # Cloud Run adds this header
            "X-Twilio-Signature": "valid_signature_for_https_url"
        }

        # Form data that Twilio sends
        form_data = {
            "CallSid": "CA1234567890",
            "From": "+15559876543",
            "To": "+12072203501"
        }
        mock_request.form = AsyncMock(return_value=form_data)

        # Mock the Twilio validator to check what URL it receives
        with patch.object(gateway_with_auth.twilio_validator, 'validate') as mock_validate:
            # The validator should receive the HTTPS URL, not HTTP
            mock_validate.return_value = True

            result = await gateway_with_auth._verify_twilio_request(mock_request)

            # Verify the validator was called with HTTPS URL
            mock_validate.assert_called_once()
            called_url = mock_validate.call_args[0][0]

            # This assertion WILL FAIL initially - the code currently passes HTTP URL
            assert called_url.startswith("https://"), \
                f"Expected HTTPS URL for signature validation, got: {called_url}"
            assert "https://westbethel-operator" in called_url
            assert result is True

    @pytest.mark.asyncio
    async def test_signature_validation_without_forwarded_proto(self, gateway_with_auth):
        """
        Test signature validation without X-Forwarded-Proto header (local dev scenario)

        This test simulates local development where:
        - Request is direct HTTP
        - No proxy headers
        - Twilio signs with HTTP URL

        This test SHOULD PASS even before the fix.
        """
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.url = "http://localhost:8000/voice/twilio/inbound"
        mock_request.headers = {
            "X-Twilio-Signature": "valid_signature_for_http_url"
        }

        form_data = {
            "CallSid": "CA1234567890",
            "From": "+15559876543",
            "To": "+15551234567"
        }
        mock_request.form = AsyncMock(return_value=form_data)

        with patch.object(gateway_with_auth.twilio_validator, 'validate') as mock_validate:
            mock_validate.return_value = True

            result = await gateway_with_auth._verify_twilio_request(mock_request)

            mock_validate.assert_called_once()
            called_url = mock_validate.call_args[0][0]

            # For local dev, HTTP is correct
            assert called_url.startswith("http://localhost")
            assert result is True

    @pytest.mark.asyncio
    async def test_signature_validation_with_real_twilio_validator(self):
        """
        Test with actual Twilio RequestValidator to ensure our URL reconstruction works

        This integration test uses the real Twilio validator library.
        """
        auth_token = "test_auth_token_12345"
        validator = RequestValidator(auth_token)

        # Simulate what Twilio would send
        url = "https://westbethel-operator-jvm6akkheq-uc.a.run.app/voice/twilio/inbound"
        params = {
            "CallSid": "CA1234567890",
            "From": "+15559876543",
            "To": "+12072203501",
            "CallStatus": "ringing"
        }

        # Generate a valid signature for the HTTPS URL
        signature = validator.compute_signature(url, params)

        # Now create a mock request that simulates Cloud Run
        mock_request = Mock(spec=Request)
        # Cloud Run gives us HTTP internally
        mock_request.url = "http://westbethel-operator-jvm6akkheq-uc.a.run.app/voice/twilio/inbound"
        mock_request.headers = {
            "X-Forwarded-Proto": "https",  # But external was HTTPS
            "X-Twilio-Signature": signature
        }
        mock_request.form = AsyncMock(return_value=params)

        # Create gateway with the same auth token
        with patch.dict('os.environ', {
            'TWILIO_ACCOUNT_SID': 'ACtest123',
            'TWILIO_AUTH_TOKEN': auth_token,
            'TWILIO_PHONE_NUMBER': '+12072203501'
        }):
            manager = Mock(spec=SessionManager)
            gateway = VoiceGateway(session_manager=manager)

            # This SHOULD return True after our fix
            result = await gateway._verify_twilio_request(mock_request)

            assert result is True, "Signature validation should pass with correct HTTPS URL reconstruction"

    @pytest.mark.asyncio
    async def test_handle_twilio_call_rejects_invalid_signature(self, gateway_with_auth):
        """
        Test that handle_twilio_call rejects requests with invalid signatures
        """
        mock_request = Mock(spec=Request)
        mock_request.url = "https://westbethel-operator-jvm6akkheq-uc.a.run.app/voice/twilio/inbound"
        mock_request.headers = {
            "X-Twilio-Signature": "invalid_signature"
        }

        form_data = {
            "CallSid": "CA1234567890",
            "From": "+15559876543",
            "To": "+12072203501"
        }
        mock_request.form = AsyncMock(return_value=form_data)

        with patch.object(gateway_with_auth.twilio_validator, 'validate') as mock_validate:
            mock_validate.return_value = False  # Invalid signature

            # Should return error TwiML, not raise exception
            response = await gateway_with_auth.handle_twilio_call(mock_request)

            # Check that it returned an error response
            assert response.status_code == 200  # Still returns 200 with error TwiML
            assert b"technical difficulties" in response.body or b"sorry" in response.body.lower()


class TestGatewayURLReconstruction:
    """Test URL reconstruction from proxy headers"""

    @pytest.mark.asyncio
    async def test_url_reconstruction_with_x_forwarded_proto(self):
        """Test that URLs are correctly reconstructed from X-Forwarded-Proto"""
        mock_request = Mock(spec=Request)
        mock_request.url = "http://example.com/voice/twilio/inbound"
        mock_request.headers = {"X-Forwarded-Proto": "https"}

        # After our fix, there should be a helper method to get the correct URL
        # For now, this is what we expect the behavior to be
        expected_url = "https://example.com/voice/twilio/inbound"

        # This will be implemented in the fix
        # reconstructed_url = _reconstruct_url_from_request(mock_request)
        # assert reconstructed_url == expected_url

    @pytest.mark.asyncio
    async def test_url_reconstruction_without_proxy_headers(self):
        """Test that URLs without proxy headers are used as-is"""
        mock_request = Mock(spec=Request)
        mock_request.url = "http://localhost:8000/voice/twilio/inbound"
        mock_request.headers = {}

        # Without proxy headers, use the URL as-is
        expected_url = "http://localhost:8000/voice/twilio/inbound"

        # This will be implemented in the fix
        # reconstructed_url = _reconstruct_url_from_request(mock_request)
        # assert reconstructed_url == expected_url
