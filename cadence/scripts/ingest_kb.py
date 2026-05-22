#!/usr/bin/env python3
"""
Ingest the Cadence knowledge base into the running backend.

Usage:
    python scripts/ingest_kb.py [--url http://localhost:5001] [--token YOUR_JWT_TOKEN]
"""
import sys
import os
import argparse
import requests

def main():
    parser = argparse.ArgumentParser(description="Ingest Cadence knowledge base")
    parser.add_argument("--url", default="http://localhost:5001", help="Backend base URL")
    parser.add_argument("--token", default=os.environ.get("CADENCE_TOKEN", ""), help="JWT auth token")
    args = parser.parse_args()

    kb_path = os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "books.md")
    kb_path = os.path.abspath(kb_path)

    if not os.path.exists(kb_path):
        print(f"Knowledge base file not found: {kb_path}")
        sys.exit(1)

    with open(kb_path, "r") as f:
        content = f.read()

    print(f"Loaded {len(content):,} characters from {kb_path}")

    if not args.token:
        print("No token provided. Set CADENCE_TOKEN env var or pass --token.")
        print("Get your token from Supabase: Auth → Users → your user → access_token")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {args.token}", "Content-Type": "application/json"}
    resp = requests.post(f"{args.url}/api/admin/ingest", json={"content": content}, headers=headers)

    if resp.ok:
        data = resp.json()
        print(f"Ingested {data['chunks_ingested']} chunks into the knowledge base.")
    else:
        print(f"Error {resp.status_code}: {resp.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
