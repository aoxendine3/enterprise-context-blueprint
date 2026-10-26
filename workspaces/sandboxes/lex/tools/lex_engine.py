# Lex: Sovereign Legal, Compliance & Smart Contract Auditor
import os, re

class ComplianceAuditorEngine:
    FORBIDDEN_TRACKERS = ["google-analytics.com", "segment.io", "sentry.io"]

    def audit_source(self, code_text):
        violations = []
        for tracker in self.FORBIDDEN_TRACKERS:
            if tracker in code_text:
                violations.append(f"LEGAL_VIOLATION_TRACKER_FOUND: {tracker}")
        return {"compliant": len(violations) == 0, "violations": violations}

if __name__ == "__main__":
    print(ComplianceAuditorEngine().audit_source("import requests; requests.get('https://sovereign.local')"))\n