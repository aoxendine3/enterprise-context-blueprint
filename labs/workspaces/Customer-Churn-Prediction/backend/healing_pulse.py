import time
import os
import psutil
from flask import g, request, jsonify

class HealingPulse:
    def __init__(self, app=None):
        self.metrics = {
            "total_requests": 0,
            "error_count": 0,
            "response_times": [],
            "latency_violations": 0
        }
        self.LATENCY_THRESHOLD_MS = 500  # Alert if request > 500ms
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
        
        # Add endpoints to the app
        app.add_url_rule('/api/pulse/health', 'pulse_health', self.health_check, methods=['GET'])
        app.add_url_rule('/api/pulse/metrics', 'pulse_metrics', self.get_metrics, methods=['GET'])

    def before_request(self):
        # Record start time for latency tracking
        g.start_time = time.time()

    def after_request(self, response):
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            elapsed_ms = int(elapsed * 1000)
            
            # Keep only the last 1000 response times to prevent memory leaks
            self.metrics["response_times"].append(elapsed_ms)
            if len(self.metrics["response_times"]) > 1000:
                self.metrics["response_times"].pop(0)
            
            if elapsed_ms > self.LATENCY_THRESHOLD_MS:
                self.metrics["latency_violations"] += 1
                
        if response.status_code >= 400 and response.status_code != 404:
            self.metrics["error_count"] += 1
            
        self.metrics["total_requests"] += 1
        return response

    def teardown_request(self, exception=None):
        if exception:
            self.metrics["error_count"] += 1

    def get_system_telemetry(self):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_usage_mb": round(mem_info.rss / (1024 * 1024), 2),
            "system_cpu_percent": psutil.cpu_percent(interval=None),
            "system_memory_percent": psutil.virtual_memory().percent
        }

    def health_check(self):
        # Basic health endpoint
        return jsonify({"status": "healthy", "pulse": "active", "timestamp": time.time()})

    def get_metrics(self):
        # Calculate avg response time
        avg_resp = 0
        if self.metrics["response_times"]:
            avg_resp = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            
        telemetry = self.get_system_telemetry()
        
        return jsonify({
            "status": "online",
            "pulse_metrics": {
                "total_requests": self.metrics["total_requests"],
                "error_count": self.metrics["error_count"],
                "average_latency_ms": round(avg_resp, 2),
                "latency_violations": self.metrics["latency_violations"],
            },
            "system_telemetry": telemetry,
            "timestamp": time.time()
        })
