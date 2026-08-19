"""
chatbot/test_chatbot.py — Test suite for the secure chatbot.

Covers:
  1. Tool function data isolation (user A can't see user B's donations)
  2. Input validation (empty, too long)
  3. Rate limiting (429 after threshold + retry_after)
  4. Authentication requirement (401/redirect for anonymous)
  5. End-to-end chat endpoint (mocked Gemini API)
  6. Error logging (ChatLog.error_details populated on failure)
  7. History trimming
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from projects.models import Project, Donation, Category
from chatbot.models import ChatLog
from chatbot.services import get_chatbot_tools


# ---------------------------------------------------------------------------
# Helper: create test users and data
# ---------------------------------------------------------------------------
class ChatbotTestBase(TestCase):
    """Base class with shared test fixtures."""

    @classmethod
    def setUpTestData(cls):
        # Create two test users
        cls.user_a = CustomUser.objects.create_user(
            email="alice@test.com",
            password="TestPass123!",
            first_name="Alice",
            last_name="Donor",
            mobile_phone="01012345678",
            is_active=True,
        )
        cls.user_b = CustomUser.objects.create_user(
            email="bob@test.com",
            password="TestPass123!",
            first_name="Bob",
            last_name="Creator",
            mobile_phone="01098765432",
            is_active=True,
        )

        # Create a category and project
        cls.category = Category.objects.create(name="Education", slug="education")
        cls.project = Project.objects.create(
            creator=cls.user_b,
            title="Build a School in Aswan",
            details="A project to build a school in Aswan governorate.",
            category=cls.category,
            total_target=Decimal("100000.00"),
            start_date="2026-01-01",
            end_date="2026-12-31",
            status=Project.Status.RUNNING,
        )

        # Alice donates to the project
        cls.donation_a = Donation.objects.create(
            project=cls.project,
            donor=cls.user_a,
            amount=Decimal("500.00"),
        )

    def setUp(self):
        """Clear cache before each test to reset rate limits."""
        cache.clear()
        self.client = Client()


# ---------------------------------------------------------------------------
# Tool Function Data Isolation Tests
# ---------------------------------------------------------------------------
class ToolDataIsolationTests(ChatbotTestBase):
    """Tests that tool functions return data scoped to the correct user."""

    def test_my_donations_returns_only_own_data(self):
        """User A's get_my_donations tool returns only user A's donations."""
        tools = get_chatbot_tools(self.user_a)
        # get_my_donations is at index 2
        get_my_donations = tools[2]
        result = get_my_donations()
        self.assertIn("recent", result)
        self.assertEqual(result["recent"][0]["amt"], 500)
        self.assertEqual(result["recent"][0]["proj"], "Build a School in Aswan")

    def test_other_user_sees_no_donations(self):
        """User B (who hasn't donated) gets an empty message."""
        tools = get_chatbot_tools(self.user_b)
        get_my_donations = tools[2]
        result = get_my_donations()
        self.assertIn("message", result)
        self.assertIn("No donations", result["message"])

    def test_my_projects_returns_only_own_data(self):
        """User B's get_my_created_campaigns tool returns only user B's projects."""
        tools = get_chatbot_tools(self.user_b)
        get_my_created = tools[7]
        result = get_my_created()
        self.assertIn("data", result)
        self.assertEqual(result["data"][0]["title"], "Build a School in Aswan")

    def test_my_projects_for_user_with_no_projects(self):
        """User A (who hasn't created projects) gets an empty message."""
        tools = get_chatbot_tools(self.user_a)
        get_my_created = tools[7]
        result = get_my_created()
        self.assertIn("message", result)
        self.assertIn("None", result["message"])

    def test_search_campaigns_returns_matching_project(self):
        """A search query returns the matching project data."""
        tools = get_chatbot_tools(self.user_a)
        search = tools[0]
        result = search(search_terms=["school", "aswan"])
        self.assertIn("data", result)
        self.assertEqual(result["data"][0]["title"], "Build a School in Aswan")

    def test_search_campaigns_no_personal_data(self):
        """Campaign search results never contain user emails or phones."""
        tools = get_chatbot_tools(self.user_a)
        search = tools[0]
        result = search(search_terms=["school"])
        result_str = str(result)
        self.assertNotIn("bob@test.com", result_str)
        self.assertNotIn("01098765432", result_str)

    def test_search_by_category(self):
        """Searching by category returns matching projects."""
        tools = get_chatbot_tools(self.user_a)
        search = tools[0]
        result = search(category="Education")
        self.assertIn("data", result)
        self.assertTrue(len(result["data"]) > 0)

    def test_search_by_status(self):
        """Searching by status returns matching projects."""
        tools = get_chatbot_tools(self.user_a)
        search = tools[0]
        result = search(status="running")
        self.assertIn("data", result)

    def test_platform_stats(self):
        """Platform stats tool returns aggregate data."""
        tools = get_chatbot_tools(self.user_a)
        stats = tools[1]
        result = stats()
        self.assertIn("total_camp", result)
        self.assertIn("raised", result)
        self.assertGreater(result["total_camp"], 0)


# ---------------------------------------------------------------------------
# Input Validation Tests
# ---------------------------------------------------------------------------
class InputValidationTests(ChatbotTestBase):
    """Tests for input validation on the chat endpoint."""

    def test_empty_message_returns_400(self):
        """An empty message returns a 400 error."""
        self.client.login(email="alice@test.com", password="TestPass123!")
        response = self.client.post(
            "/api/chat/",
            data='{"message": ""}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("empty", response.json()["error"].lower())

    def test_whitespace_only_message_returns_400(self):
        """A whitespace-only message returns a 400 error."""
        self.client.login(email="alice@test.com", password="TestPass123!")
        response = self.client.post(
            "/api/chat/",
            data='{"message": "   "}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_oversized_message_returns_400(self):
        """A message exceeding 500 chars returns a 400 error."""
        self.client.login(email="alice@test.com", password="TestPass123!")
        long_message = "a" * 501
        response = self.client.post(
            "/api/chat/",
            data=f'{{"message": "{long_message}"}}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("too long", response.json()["error"].lower())

    def test_invalid_json_returns_400(self):
        """Malformed JSON returns a 400 error."""
        self.client.login(email="alice@test.com", password="TestPass123!")
        response = self.client.post(
            "/api/chat/",
            data="not json at all",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------
class AuthenticationTests(ChatbotTestBase):
    """Tests that anonymous users cannot access the chat endpoint."""

    def test_anonymous_user_redirected(self):
        """An unauthenticated POST to the chat endpoint is redirected to login."""
        response = self.client.post(
            "/api/chat/",
            data='{"message": "hello"}',
            content_type="application/json",
        )
        # @login_required redirects to the login page (302)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())


# ---------------------------------------------------------------------------
# Rate Limiting Tests
# ---------------------------------------------------------------------------
class RateLimitTests(ChatbotTestBase):
    """Tests for the per-user rate limiter."""

    @patch("chatbot.views.genai")
    def test_rate_limit_kicks_in(self, mock_genai):
        """After 20 requests, the 21st returns a 429 status with retry_after."""
        # Mock the Gemini chat session
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_chat.send_message.return_value = mock_response
        mock_genai.Client.return_value.chats.create.return_value = mock_chat

        self.client.login(email="alice@test.com", password="TestPass123!")

        # Send 20 valid requests (should all succeed)
        for i in range(20):
            response = self.client.post(
                "/api/chat/",
                data='{"message": "hello"}',
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200, f"Request {i+1} failed unexpectedly")

        # 21st request should be rate-limited
        response = self.client.post(
            "/api/chat/",
            data='{"message": "hello"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 429)
        data = response.json()
        self.assertIn("too many", data["error"].lower())
        self.assertIn("retry_after", data)


# ---------------------------------------------------------------------------
# ChatLog Tests
# ---------------------------------------------------------------------------
class ChatLogTests(ChatbotTestBase):
    """Tests that interactions are properly logged."""

    @patch("chatbot.views.genai")
    def test_successful_chat_is_logged(self, mock_genai):
        """A successful chat interaction creates a ChatLog entry."""
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Here is the information about the campaign."
        mock_chat.send_message.return_value = mock_response
        mock_genai.Client.return_value.chats.create.return_value = mock_chat

        self.client.login(email="alice@test.com", password="TestPass123!")
        self.client.post(
            "/api/chat/",
            data='{"message": "Tell me about school"}',
            content_type="application/json",
        )

        self.assertEqual(ChatLog.objects.count(), 1)
        log = ChatLog.objects.first()
        self.assertEqual(log.user, self.user_a)
        self.assertIn("school", log.message.lower())
        self.assertFalse(log.was_refused)
        self.assertEqual(log.error_details, "")

    @patch("chatbot.views.genai")
    def test_api_error_logs_full_traceback(self, mock_genai):
        """If the Gemini API fails, the full traceback is stored in ChatLog.error_details."""
        mock_genai.Client.return_value.chats.create.side_effect = Exception("API connection refused")

        self.client.login(email="alice@test.com", password="TestPass123!")
        response = self.client.post(
            "/api/chat/",
            data='{"message": "hello"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn("try again", response.json()["error"].lower())

        # Verify full error is logged
        self.assertEqual(ChatLog.objects.count(), 1)
        log = ChatLog.objects.first()
        self.assertIn("API connection refused", log.error_details)
        self.assertIn("Traceback", log.error_details)
        self.assertEqual(log.intent, "error")


# ---------------------------------------------------------------------------
# End-to-End Chat Tests (with mocked Gemini)
# ---------------------------------------------------------------------------
class EndToEndChatTests(ChatbotTestBase):
    """Integration tests for the full chat flow with mocked Gemini API."""

    @patch("chatbot.views.genai")
    def test_legitimate_question_succeeds(self, mock_genai):
        """A valid platform question returns a 200 with a reply."""
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "The school campaign has raised 500 EGP."
        mock_chat.send_message.return_value = mock_response
        mock_genai.Client.return_value.chats.create.return_value = mock_chat

        self.client.login(email="alice@test.com", password="TestPass123!")
        response = self.client.post(
            "/api/chat/",
            data='{"message": "Tell me about the school project"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", response.json())

    @patch("chatbot.views.genai")
    def test_api_error_returns_500_gracefully(self, mock_genai):
        """If the Gemini API fails, the user gets a clean error."""
        mock_genai.Client.return_value.chats.create.side_effect = Exception("API down")

        self.client.login(email="alice@test.com", password="TestPass123!")
        response = self.client.post(
            "/api/chat/",
            data='{"message": "hello"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn("try again", response.json()["error"].lower())
        # Error should still be logged
        self.assertEqual(ChatLog.objects.count(), 1)

    @patch("chatbot.views.genai")
    def test_history_is_trimmed_server_side(self, mock_genai):
        """History longer than MAX_HISTORY_LENGTH is trimmed before passing to Gemini."""
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_chat.send_message.return_value = mock_response
        mock_genai.Client.return_value.chats.create.return_value = mock_chat

        self.client.login(email="alice@test.com", password="TestPass123!")

        # Send a history with 20 entries (should be trimmed to 10)
        long_history = [
            {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": f"msg {i}"}]}
            for i in range(20)
        ]
        import json
        self.client.post(
            "/api/chat/",
            data=json.dumps({"message": "hello", "history": long_history}),
            content_type="application/json",
        )

        # Verify that chats.create was called with trimmed history
        call_kwargs = mock_genai.Client.return_value.chats.create.call_args
        passed_history = call_kwargs.kwargs.get("history", [])
        self.assertLessEqual(len(passed_history), 10)

    @patch("chatbot.views.genai")
    def test_quota_error_returns_friendly_message(self, mock_genai):
        """A 429 quota error from Gemini returns a friendly reply, not a 500."""
        mock_genai.Client.return_value.chats.create.side_effect = Exception("429 Resource exhausted: quota exceeded")

        self.client.login(email="alice@test.com", password="TestPass123!")
        response = self.client.post(
            "/api/chat/",
            data='{"message": "hello"}',
            content_type="application/json",
        )

        # Should return 200 with a friendly reply, not a 500
        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", response.json())
        self.assertIn("too many requests", response.json()["reply"].lower())
