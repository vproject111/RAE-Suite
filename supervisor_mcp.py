import time
import os
import subprocess
import urllib.request
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# Configuration
BASE_API_URL = os.getenv("RAE_API_URL", "http://localhost:8000").rstrip("/")
API_URL = f"{BASE_API_URL}/v2/memories/"
HEADERS = {
    "X-API-Key": os.getenv("RAE_API_KEY", "test-key"),
    "X-Tenant-Id": os.getenv("RAE_TENANT_ID", "00000000-0000-0000-0000-000000000000"),
}
WORK_DIR = os.getenv("RAE_WORK_DIR", "/app/agent_hive/work_dir/components/")
COMPOSE_DIR = os.getenv("RAE_COMPOSE_DIR", "/app/agent_hive/")

# SMTP Configuration (Injected via Environment Variables)
SMTP_SERVER = os.getenv("RAE_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("RAE_SMTP_PORT", "587"))
SMTP_USER = os.getenv("RAE_SMTP_USER")
SMTP_PASS = os.getenv("RAE_SMTP_PASS")
REPORT_EMAIL = os.getenv("RAE_REPORT_EMAIL", "vproject.111@gmail.com")


def log_to_rae(msg, tags=None):
    if tags is None:
        tags = []
    payload = {"content": f"[SUPERVISOR] {msg}", "layer": "reflective", "tags": ["supervisor_log"] + list(tags)}
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={"Content-Type": "application/json", **HEADERS},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def send_email(subject, body):
    if not SMTP_USER or not SMTP_PASS:
        print(f"Skipping email (no credentials): {subject}")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = REPORT_EMAIL
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        log_to_rae(f"Email sent: {subject}", ["email_sent"])
    except Exception as e:
        log_to_rae(f"Email failed: {e}", ["error"])


def get_stats():
    try:
        tsx_count = len([f for f in os.listdir(WORK_DIR) if f.endswith(".tsx")])
    except Exception:
        tsx_count = 0

    try:
        res = subprocess.check_output(
            ["psql", "-U", "rae", "-d", "rae", "-t", "-c", "SELECT count(*) FROM memory_neighbors;"],
            shell=False,
            stderr=subprocess.DEVNULL,
        )
        graph_count = int(res.decode("utf-8").strip())
    except Exception:
        graph_count = 0

    try:
        res = subprocess.check_output(
            ["psql", "-U", "rae", "-d", "rae", "-t", "-c", "SELECT count(*) FROM memories WHERE layer = 'semantic';"],
            shell=False,
            stderr=subprocess.DEVNULL,
        )
        mem_count = int(res.decode("utf-8").strip())
    except Exception:
        mem_count = 0

    return tsx_count, graph_count, mem_count


def run_supervisor_loop():
    last_tsx, last_graph, last_mem = get_stats()
    last_report_time = time.time()

    print("Supervisor LTS v2.3 active. Monitoring Oracle Graph & Dreamsoft Factory...")
    log_to_rae(f"Supervisor LTS v2.3 started. Reporting configured to {REPORT_EMAIL}")
    send_email("RAE Factory: Supervisor Online", "RAE Factory Supervisor has been restored and is monitoring progress.")

    while True:
        time.sleep(300)
        current_tsx, current_graph, current_mem = get_stats()
        now = time.time()

        if now - last_report_time >= 7200:
            report = (
                f"Periodic Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"- Generated Components: {current_tsx}\n"
                f"- Knowledge Graph Edges: {current_graph}\n"
                f"- Semantic Memories: {current_mem}\n"
                f"- System State: Operational"
            )
            log_to_rae(report, ["periodic_report"])
            send_email("RAE Factory: 2h Status Update", report)
            last_report_time = now

        if current_tsx == last_tsx and current_graph == last_graph and current_mem == last_mem:
            msg = "Potential STALL detected. No progress in 5 mins."
            log_to_rae(msg, ["warning", "stall_check"])

        if current_tsx > last_tsx or current_graph > last_graph or current_mem > last_mem:
            log_to_rae(f"Progress: TSX={current_tsx}, Graph={current_graph}, Mem={current_mem}", ["progress"])
            last_tsx, last_graph, last_mem = current_tsx, current_graph, current_mem


if __name__ == "__main__":
    run_supervisor_loop()

