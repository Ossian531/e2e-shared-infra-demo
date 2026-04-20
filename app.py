"""Tiny demo app that verifies shared infrastructure connectivity."""

import os
import socket
from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI()

DB_HOST = os.environ.get("DB_HOST", "")
DB_USER = os.environ.get("DB_USER", "")
EFS_PATH = os.environ.get("EFS_PATH", "/mnt/data")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")


def check_db():
    if not DB_HOST:
        return {"status": "skip", "reason": "DB_HOST not set"}
    try:
        host = DB_HOST.split(":")[0]
        port = int(DB_HOST.split(":")[1]) if ":" in DB_HOST else 5432
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        return {"status": "ok", "host": host, "port": port}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_efs():
    try:
        test_file = os.path.join(EFS_PATH, "healthcheck.txt")
        now = datetime.now(timezone.utc).isoformat()
        with open(test_file, "w") as f:
            f.write(now)
        with open(test_file) as f:
            content = f.read()
        return {"status": "ok", "path": EFS_PATH, "written": content}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_s3():
    if not BUCKET_NAME:
        return {"status": "skip", "reason": "BUCKET_NAME not set"}
    try:
        import boto3
        s3 = boto3.client("s3")
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=1)
        return {"status": "ok", "bucket": BUCKET_NAME, "key_count": resp.get("KeyCount", 0)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/")
def root():
    return {"service": "e2e-shared-infra-demo", "status": "running"}


@app.get("/health")
def health():
    return {
        "db": check_db(),
        "efs": check_efs(),
        "s3": check_s3(),
    }
