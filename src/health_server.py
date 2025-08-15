"""
Health check server for Cloud Run
"""

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

from .utils import get_logger


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check endpoints"""

    def __init__(self, *args, bot_instance=None, **kwargs):
        self.bot_instance = bot_instance
        self.logger = get_logger("health_server")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/ready":
            self._handle_ready()
        elif self.path == "/metrics":
            self._handle_metrics()
        else:
            self._send_response(404, {"error": "Not Found"})

    def _handle_health(self):
        """Basic health check - always returns healthy if server is running"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "discord-obsidian-memo-bot",
            "version": "0.1.0",
        }
        self._send_response(200, health_data)

    def _handle_ready(self):
        """Readiness check - checks if bot is connected and operational"""
        if not self.bot_instance:
            self._send_response(
                503, {"status": "not_ready", "reason": "bot_not_initialized"}
            )
            return

        if not self.bot_instance.is_ready:
            self._send_response(
                503, {"status": "not_ready", "reason": "bot_not_connected"}
            )
            return

        ready_data = {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "bot_connected": True,
            "guild_connected": self.bot_instance.guild is not None,
            "uptime_seconds": (
                datetime.now() - self.bot_instance._start_time
            ).total_seconds(),
        }
        self._send_response(200, ready_data)

    def _handle_metrics(self):
        """Expose basic metrics for monitoring"""
        if not self.bot_instance:
            self._send_response(503, {"error": "bot_not_available"})
            return

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (
                datetime.now() - self.bot_instance._start_time
            ).total_seconds(),
            "bot_status": {
                "connected": self.bot_instance.is_ready,
                "guild_count": len(self.bot_instance.client.guilds)
                if hasattr(self.bot_instance.client, "guilds")
                else 0,
            },
        }

        # Add system metrics if available
        if hasattr(self.bot_instance, "system_metrics"):
            metrics["system_metrics"] = (
                self.bot_instance.system_metrics.get_system_health_status()
            )

        # Add API usage metrics if available
        if hasattr(self.bot_instance, "api_usage_monitor"):
            metrics["api_usage"] = (
                self.bot_instance.api_usage_monitor.get_usage_dashboard()
            )

        self._send_response(200, metrics)

    def _send_response(self, status_code: int, data: dict[str, Any]):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        response_body = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_body.encode("utf-8"))

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr"""
        self.logger.debug(f"Health server: {format % args}")


class HealthServer:
    """Health check server for Cloud Run deployment"""

    def __init__(self, bot_instance=None, port: int = 8080):
        self.bot_instance = bot_instance
        self.port = port
        self.server = None
        self.thread = None
        self.logger = get_logger("health_server")

    def start(self):
        """Start the health check server"""

        def handler(*args, **kwargs):
            return HealthCheckHandler(*args, bot_instance=self.bot_instance, **kwargs)

        try:
            self.server = HTTPServer(("0.0.0.0", self.port), handler)
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()

            self.logger.info(f"Health check server started on port {self.port}")
            self.logger.info("Available endpoints:")
            self.logger.info("  - GET /health  - Basic health check")
            self.logger.info("  - GET /ready   - Readiness probe")
            self.logger.info("  - GET /metrics - Application metrics")

        except Exception as e:
            self.logger.error(f"Failed to start health server: {e}")
            raise

    def stop(self):
        """Stop the health check server"""
        if self.server:
            self.logger.info("Stopping health check server")
            self.server.shutdown()
            self.server.server_close()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

        self.logger.info("Health check server stopped")
