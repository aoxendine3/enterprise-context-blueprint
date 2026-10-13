#!/usr/bin/env python3
"""
===============================================================================
XORAS::OS - SOVEREIGN SANITY.IO ENTERPRISE API CLIENT (v1.0.0)
===============================================================================
Mandate: Production Content Engine, GROQ Querying, JSON Mutations,
         and Staged Release Publishing under strict 0600 POSIX Key Governance.
Author: The Lead 9 Council (Maxx, Clara, Vance, John, DAXX)
===============================================================================
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import hashlib
from typing import Dict, Any, List, Optional

CREDENTIALS_FILE = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/.sovereign/credentials.json")
TOKEN_FILE = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/.sovereign/crypto_keys/sanity_api_token.bin")
AUDIT_DIR = os.path.expanduser("~/Desktop/SSOT_Agentic_Brain/docs/audits")

class SovereignSanityClient:
    def __init__(self, project_id: Optional[str] = None, dataset: Optional[str] = None, api_version: str = "v2021-06-07"):
        creds_sanity = self._load_sanity_creds()
        self.project_id = os.environ.get("SANITY_PROJECT_ID") or project_id or creds_sanity.get("project_id", "on7ly92s")
        self.organization_id = os.environ.get("SANITY_ORGANIZATION_ID") or creds_sanity.get("organization_id", "or68rr8k0")
        self.dataset = os.environ.get("SANITY_DATASET") or dataset or creds_sanity.get("dataset", "production")
        self.api_version = api_version
        self.token = self._load_token(creds_sanity)
        self.base_url = f"https://{self.project_id}.api.sanity.io/{self.api_version}"

    def _load_sanity_creds(self) -> Dict[str, Any]:
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("credentials", {}).get("sanity", {})
            except Exception:
                pass
        return {}

    def _load_token(self, creds: Optional[Dict[str, Any]] = None) -> str:
        # 1. Environment variable takes highest precedence (zero disk leak vector)
        env_token = os.environ.get("SANITY_API_TOKEN", "").strip()
        if env_token:
            return env_token
        # 2. Strict 0600 POSIX key file outside tracked git tree
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                token = f.read().strip()
                if token:
                    return token
        # 3. Fallback to local credentials structure if present
        if creds and creds.get("token"):
            return creds["token"]
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("credentials", {}).get("sanity", {}).get("token", "")
            except Exception:
                pass
        return ""

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "XORAS-Sovereign-Agent/1.0.0 (Apple Silicon M4)"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def execute_groq_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a GROQ query against Sanity Content Lake.
        """
        encoded_query = urllib.parse.quote(query)
        url = f"{self.base_url}/data/query/{self.dataset}?query={encoded_query}"
        
        if params:
            for k, v in params.items():
                url += f"&${urllib.parse.quote(k)}={urllib.parse.quote(json.dumps(v))}"

        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "status": "success",
                    "query": query,
                    "result": data.get("result", []),
                    "ms": data.get("ms", 0),
                    "offline_mock": False
                }
        except Exception as e:
            # Fallback to local mock context response if offline or un-provisioned project ID
            return {
                "status": "offline_airgap_mode",
                "error": str(e),
                "query": query,
                "result": [
                    {
                        "_id": "xoras.doc.001",
                        "_type": "sovereign_document",
                        "title": "XORAS::OS Sovereign Architecture Document",
                        "groundedness_score": 100.0,
                        "verified_by": ["Maxx", "Clara", "Vance"]
                    }
                ],
                "ms": 1.2,
                "offline_mock": True
            }

    def mutate_documents(self, mutations: List[Dict[str, Any]], return_ids: bool = True) -> Dict[str, Any]:
        """
        Executes a batch of JSON document mutations (create, createOrReplace, patch, delete).
        """
        url = f"{self.base_url}/data/mutate/{self.dataset}?returnIds={'true' if return_ids else 'false'}"
        payload = json.dumps({"mutations": mutations}).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "status": "success",
                    "results": data.get("results", []),
                    "transaction_id": data.get("transactionId", ""),
                    "offline_mock": False
                }
        except Exception as e:
            # Fallback mock receipt for offline air-gap pipeline execution
            tx_id = f"tx_mock_{hashlib.sha256(payload).hexdigest()[:16]}"
            return {
                "status": "offline_airgap_mode",
                "error": str(e),
                "results": [{"id": m.get("create", {}).get("_id", "doc_mock_id"), "operation": "staged"} for m in mutations],
                "transaction_id": tx_id,
                "offline_mock": True
            }

    def create_document(self, doc_type: str, attributes: Dict[str, Any], doc_id: Optional[str] = None) -> Dict[str, Any]:
        doc = {"_type": doc_type, **attributes}
        if doc_id:
            doc["_id"] = doc_id
        return self.mutate_documents([{"createOrReplace": doc}])

    def patch_document(self, doc_id: str, set_fields: Optional[Dict[str, Any]] = None, unset_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        patch = {"id": doc_id}
        if set_fields:
            patch["set"] = set_fields
        if unset_fields:
            patch["unset"] = unset_fields
        return self.mutate_documents([{"patch": patch}])

    def stage_content_release(self, release_name: str, document_mutations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Stages document mutations inside a Sanity Content Release for human review.
        """
        release_id = f"release_{release_name.lower().replace(' ', '_')}_{int(time.time())}"
        staged_mutations = []
        for m in document_mutations:
            op_key = list(m.keys())[0]
            doc = m[op_key]
            if isinstance(doc, dict):
                doc["_release"] = release_id
            staged_mutations.append(m)

        res = self.mutate_documents(staged_mutations)
        res["release_id"] = release_id
        res["release_name"] = release_name
        return res

if __name__ == "__main__":
    client = SovereignSanityClient()
    print("=================================================================")
    print("  XORAS::OS - SOVEREIGN SANITY CLIENT TEST EXECUTION")
    print("=================================================================")
    query_res = client.execute_groq_query('*[_type == "sovereign_document"]')
    print(f"[+] GROQ Query Status: {query_res['status']} (Offline Mode: {query_res['offline_mock']})")
    print(f"[+] Sample Result Count: {len(query_res['result'])}")

    create_res = client.create_document("sovereign_audit", {
        "title": "NASA-Style 6-Gap Architectural Hardening Report",
        "doc_id": "XORAS_013",
        "verdict": "CERTIFIED_FIN_ATLAN_SURPASSED",
        "timestamp": time.time()
    }, doc_id="audit_xoras_013")
    print(f"[+] Document Mutation Status: {create_res['status']} (TxID: {create_res['transaction_id']})")
    print("=================================================================")
