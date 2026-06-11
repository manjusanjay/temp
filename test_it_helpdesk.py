import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'it-helpdesk-agent', 'it-helpdesk-agent'))

# ─────────────────────────────────────────────
# AGENT.PY TESTS
# ─────────────────────────────────────────────

from agent import create_ticket, check_ticket_status, escalate_ticket, execute_tool, tickets_db

class TestCreateTicket:
    def setup_method(self):
        tickets_db.clear()

    def test_create_ticket_returns_ticket_id(self):
        result = create_ticket("VPN not connecting", "P2")
        assert "ticket_id" in result
        assert result["ticket_id"].startswith("TKT-")

    def test_create_ticket_stores_correct_summary(self):
        result = create_ticket("Outlook is slow", "P3")
        assert result["summary"] == "Outlook is slow"

    def test_create_ticket_stores_correct_priority(self):
        result = create_ticket("Laptop not booting", "P1")
        assert result["priority"] == "P1"

    def test_create_ticket_default_status_is_open(self):
        result = create_ticket("Email issue", "P3")
        assert result["status"] == "Open"

    def test_create_ticket_assigned_to_helpdesk(self):
        result = create_ticket("VPN issue", "P2")
        assert result["assigned_to"] == "IT Helpdesk Team"

    def test_create_ticket_saved_in_db(self):
        result = create_ticket("Test issue", "P3")
        ticket_id = result["ticket_id"]
        assert ticket_id in tickets_db

    def test_create_ticket_generates_unique_ids(self):
        result1 = create_ticket("Issue 1", "P3")
        result2 = create_ticket("Issue 2", "P3")
        assert result1["ticket_id"] != result2["ticket_id"]

    def test_create_ticket_with_custom_user(self):
        result = create_ticket("VPN issue", "P2", user_name="John Doe")
        assert result["created_by"] == "John Doe"

    def test_create_ticket_has_created_at(self):
        result = create_ticket("Test", "P3")
        assert "created_at" in result
        assert result["created_at"] is not None


class TestCheckTicketStatus:
    def setup_method(self):
        tickets_db.clear()

    def test_check_existing_ticket(self):
        ticket = create_ticket("VPN issue", "P2")
        ticket_id = ticket["ticket_id"]
        result = check_ticket_status(ticket_id)
        assert result["ticket_id"] == ticket_id

    def test_check_nonexistent_ticket_returns_error(self):
        result = check_ticket_status("TKT-999999")
        assert "error" in result

    def test_check_ticket_returns_correct_status(self):
        ticket = create_ticket("Email issue", "P3")
        ticket_id = ticket["ticket_id"]
        result = check_ticket_status(ticket_id)
        assert result["status"] == "Open"

    def test_check_ticket_returns_correct_summary(self):
        ticket = create_ticket("Laptop slow", "P3")
        ticket_id = ticket["ticket_id"]
        result = check_ticket_status(ticket_id)
        assert result["summary"] == "Laptop slow"

    def test_check_ticket_error_message_contains_ticket_id(self):
        result = check_ticket_status("TKT-000000")
        assert "TKT-000000" in result["error"]


class TestEscalateTicket:
    def setup_method(self):
        tickets_db.clear()

    def test_escalate_existing_ticket(self):
        ticket = create_ticket("Critical VPN issue", "P1")
        ticket_id = ticket["ticket_id"]
        result = escalate_ticket(ticket_id, "Issue unresolved for 2 hours")
        assert result["status"] == "Escalated"

    def test_escalate_assigns_to_senior_engineer(self):
        ticket = create_ticket("Critical issue", "P1")
        ticket_id = ticket["ticket_id"]
        result = escalate_ticket(ticket_id, "Critical")
        assert result["assigned_to"] == "Senior IT Engineer"

    def test_escalate_saves_reason(self):
        ticket = create_ticket("VPN issue", "P2")
        ticket_id = ticket["ticket_id"]
        reason = "User reported data loss"
        result = escalate_ticket(ticket_id, reason)
        assert result["escalation_reason"] == reason

    def test_escalate_nonexistent_ticket_returns_error(self):
        result = escalate_ticket("TKT-999999", "Some reason")
        assert "error" in result

    def test_escalate_updates_ticket_in_db(self):
        ticket = create_ticket("Issue", "P1")
        ticket_id = ticket["ticket_id"]
        escalate_ticket(ticket_id, "Critical")
        assert tickets_db[ticket_id]["status"] == "Escalated"

    def test_escalate_has_escalated_at_timestamp(self):
        ticket = create_ticket("Issue", "P1")
        ticket_id = ticket["ticket_id"]
        result = escalate_ticket(ticket_id, "Critical")
        assert "escalated_at" in result


class TestExecuteTool:
    def setup_method(self):
        tickets_db.clear()

    def test_execute_create_ticket_tool(self):
        result = execute_tool("create_ticket", {
            "issue_summary": "VPN not connecting",
            "priority": "P2"
        })
        assert "ticket_id" in result
        assert result["ticket_id"].startswith("TKT-")

    def test_execute_check_ticket_status_tool(self):
        ticket = create_ticket("Test issue", "P3")
        ticket_id = ticket["ticket_id"]
        result = execute_tool("check_ticket_status", {"ticket_id": ticket_id})
        assert result["ticket_id"] == ticket_id

    def test_execute_escalate_ticket_tool(self):
        ticket = create_ticket("Critical issue", "P1")
        ticket_id = ticket["ticket_id"]
        result = execute_tool("escalate_ticket", {
            "ticket_id": ticket_id,
            "reason": "Unresolved for 2 hours"
        })
        assert result["status"] == "Escalated"

    def test_execute_unknown_tool_returns_error(self):
        result = execute_tool("unknown_tool", {})
        assert "error" in result

    def test_execute_create_ticket_with_default_priority(self):
        result = execute_tool("create_ticket", {
            "issue_summary": "Some issue"
        })
        assert "ticket_id" in result


# ─────────────────────────────────────────────
# APP.PY TESTS
# ─────────────────────────────────────────────

class TestFlaskApp:
    def setup_method(self):
        tickets_db.clear()

    @pytest.fixture
    def client(self):
        with patch('app.GEMINI_API_KEY', 'fake-key'), \
             patch('app.search') as mock_search, \
             patch('app.model') as mock_model:

            mock_search.return_value = [
                {"content": "VPN solution steps", "source": "vpn_issues.txt", "distance": 0.1}
            ]
            mock_response = MagicMock()
            mock_response.text = "Please try these VPN troubleshooting steps."
            mock_model.generate_content.return_value = mock_response

            from app import app
            app.config['TESTING'] = True
            with app.test_client() as client:
                yield client, mock_search, mock_model

    def test_chat_endpoint_returns_200(self, client):
        c, _, _ = client
        response = c.post('/chat',
            data=json.dumps({"message": "My VPN is not connecting"}),
            content_type='application/json'
        )
        assert response.status_code == 200

    def test_chat_endpoint_returns_response_field(self, client):
        c, _, _ = client
        response = c.post('/chat',
            data=json.dumps({"message": "My VPN is not connecting"}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert "response" in data

    def test_chat_endpoint_returns_rag_results(self, client):
        c, _, _ = client
        response = c.post('/chat',
            data=json.dumps({"message": "My VPN is not connecting"}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert "rag_results" in data

    def test_chat_endpoint_calls_rag_search(self, client):
        c, mock_search, _ = client
        c.post('/chat',
            data=json.dumps({"message": "My VPN is not connecting"}),
            content_type='application/json'
        )
        mock_search.assert_called_once_with("My VPN is not connecting", top_k=2)

    def test_chat_endpoint_empty_message_returns_400(self, client):
        c, _, _ = client
        response = c.post('/chat',
            data=json.dumps({"message": ""}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_reset_endpoint_clears_history(self, client):
        c, _, _ = client
        c.post('/chat',
            data=json.dumps({"message": "My VPN is not connecting"}),
            content_type='application/json'
        )
        response = c.post('/reset')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "Conversation reset"

    def test_chat_endpoint_returns_context_length(self, client):
        c, _, _ = client
        response = c.post('/chat',
            data=json.dumps({"message": "My VPN is not connecting"}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        assert "context_length" in data

    def test_chat_context_grows_with_messages(self, client):
        c, _, _ = client
        response1 = c.post('/chat',
            data=json.dumps({"message": "My VPN is not connecting"}),
            content_type='application/json'
        )
        data1 = json.loads(response1.data)
        first_context = data1["context_length"]

        response2 = c.post('/chat',
            data=json.dumps({"message": "Still not working"}),
            content_type='application/json'
        )
        data2 = json.loads(response2.data)
        second_context = data2["context_length"]

        assert second_context > first_context

    def test_chat_no_api_key_returns_500(self):
        with patch('app.GEMINI_API_KEY', ''):
            from app import app
            app.config['TESTING'] = True
            with app.test_client() as c:
                response = c.post('/chat',
                    data=json.dumps({"message": "test"}),
                    content_type='application/json'
                )
                assert response.status_code == 500


# ─────────────────────────────────────────────
# RAG ENGINE TESTS
# ─────────────────────────────────────────────

class TestRagEngine:

    @patch('rag_engine.collection')
    @patch('rag_engine.embedding_model')
    def test_search_returns_list(self, mock_embedding, mock_collection):
        mock_embedding.encode.return_value = MagicMock()
        mock_embedding.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
        mock_collection.query.return_value = {
            'documents': [["VPN solution content"]],
            'metadatas': [[{"source": "vpn_issues.txt"}]],
            'distances': [[0.15]]
        }
        from rag_engine import search
        results = search("VPN not connecting")
        assert isinstance(results, list)

    @patch('rag_engine.collection')
    @patch('rag_engine.embedding_model')
    def test_search_returns_correct_source(self, mock_embedding, mock_collection):
        mock_embedding.encode.return_value = MagicMock()
        mock_embedding.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
        mock_collection.query.return_value = {
            'documents': [["VPN solution content"]],
            'metadatas': [[{"source": "vpn_issues.txt"}]],
            'distances': [[0.15]]
        }
        from rag_engine import search
        results = search("VPN not connecting")
        assert results[0]["source"] == "vpn_issues.txt"

    @patch('rag_engine.collection')
    @patch('rag_engine.embedding_model')
    def test_search_returns_distance(self, mock_embedding, mock_collection):
        mock_embedding.encode.return_value = MagicMock()
        mock_embedding.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
        mock_collection.query.return_value = {
            'documents': [["VPN solution content"]],
            'metadatas': [[{"source": "vpn_issues.txt"}]],
            'distances': [[0.15]]
        }
        from rag_engine import search
        results = search("VPN not connecting")
        assert "distance" in results[0]

    @patch('rag_engine.collection')
    @patch('rag_engine.embedding_model')
    def test_search_returns_content(self, mock_embedding, mock_collection):
        mock_embedding.encode.return_value = MagicMock()
        mock_embedding.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
        mock_collection.query.return_value = {
            'documents': [["VPN solution content"]],
            'metadatas': [[{"source": "vpn_issues.txt"}]],
            'distances': [[0.15]]
        }
        from rag_engine import search
        results = search("VPN not connecting")
        assert results[0]["content"] == "VPN solution content"

    @patch('rag_engine.collection')
    @patch('rag_engine.embedding_model')
    def test_search_top_k_limits_results(self, mock_embedding, mock_collection):
        mock_embedding.encode.return_value = MagicMock()
        mock_embedding.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
        mock_collection.query.return_value = {
            'documents': [["Doc 1", "Doc 2"]],
            'metadatas': [[{"source": "vpn_issues.txt"}, {"source": "email_issues.txt"}]],
            'distances': [[0.1, 0.2]]
        }
        from rag_engine import search
        results = search("some query", top_k=2)
        assert len(results) == 2

    @patch('rag_engine.collection')
    @patch('rag_engine.embedding_model')
    def test_search_calls_embedding_model(self, mock_embedding, mock_collection):
        mock_embedding.encode.return_value = MagicMock()
        mock_embedding.encode.return_value.tolist.return_value = [[0.1, 0.2, 0.3]]
        mock_collection.query.return_value = {
            'documents': [["content"]],
            'metadatas': [[{"source": "vpn_issues.txt"}]],
            'distances': [[0.1]]
        }
        from rag_engine import search
        search("VPN issue")
        mock_embedding.encode.assert_called_once()
