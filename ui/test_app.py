import os
import unittest
from unittest.mock import patch, Mock

os.environ.setdefault("CRAFTY_API_TOKEN", "test-token")
import app as app_module  # noqa: E402


def mock_response(json_data, status=200):
    r = Mock()
    r.json.return_value = json_data
    r.raise_for_status = Mock()
    r.status_code = status
    return r


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_server_action_rejects_unknown_action(self):
        resp = self.client.post("/api/servers/abc/delete_everything")
        self.assertEqual(resp.status_code, 400)

    @patch.object(app_module, "crafty")
    def test_servers_maps_crafty_fields(self, crafty):
        crafty.return_value = [
            {
                "server_id": "1",
                "server_name": "survival",
                "server_port": 25565,
                "running": True,
            }
        ]
        resp = self.client.get("/api/servers")
        self.assertEqual(
            resp.get_json(),
            [{"id": "1", "name": "survival", "port": 25565, "running": True}],
        )

    @patch("app.requests")
    def test_connect_tears_down_existing_tunnel_before_starting_new(self, requests):
        requests.get.return_value = mock_response(
            {"tunnels": [{"proto": "tcp", "name": "old", "config": {"addr": "x:1"}}]}
        )
        requests.post.return_value = mock_response({"public_url": "tcp://host:1234"})
        requests.delete.return_value = mock_response({})

        resp = self.client.post("/api/connect", json={"port": 25566})

        requests.delete.assert_called_once_with(
            f"{app_module.NGROK_API}/old", timeout=5
        )
        self.assertEqual(resp.get_json(), {"address": "host:1234"})

    @patch("app.requests")
    def test_status_reports_no_tunnel(self, requests):
        requests.get.return_value = mock_response({"tunnels": []})
        resp = self.client.get("/api/status")
        self.assertEqual(resp.get_json(), {"connected": None, "address": None})


if __name__ == "__main__":
    unittest.main()
