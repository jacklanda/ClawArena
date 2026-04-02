#!/usr/bin/env python3
"""
Run all ClawArena email tasks through the OpenClaw Gateway agent,
send each composed email via Gmail SMTP, and evaluate with the rubric scorer.
"""

from __future__ import annotations

import asyncio
import json
import os
import smtplib
import ssl
import subprocess
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ── resolve project root so src/ is importable ───────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from clawarena.core.agent import AgentResponse
from clawarena.core.task import Task, TaskCategory
from clawarena.evaluators import get_evaluator_registry
from clawarena.tasks.registry import TaskRegistry

# ── SMTP / addressing constants ───────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
GMAIL_SENDER  = os.environ.get("GMAIL_SENDER",   "yonyonlau@gmail.com")
GMAIL_RECEIVER= os.environ.get("GMAIL_RECEIVER", "yangliu.real@gmail.com")
GMAIL_PASSWORD= os.environ.get("GMAIL_APP_PASSWORD", "ocmnclxvlvuxhuar")

SEPARATOR = "─" * 60


# ── helpers ───────────────────────────────────────────────────────────────────

def call_openclaw_agent(message: str, timeout: int = 180) -> tuple[str, dict]:
    """
    Send *message* to the running OpenClaw Gateway agent and return
    (response_text, usage_dict).
    """
    result = subprocess.run(
        ["openclaw", "agent", "--agent", "main", "--message", message, "--json"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    raw = result.stdout

    # Strip leading config-warning lines before first '{'.
    json_start = raw.find("{")
    if json_start == -1:
        return raw.strip(), {}

    try:
        data = json.loads(raw[json_start:])
    except json.JSONDecodeError:
        return raw.strip(), {}

    # Navigate result.payloads[*].text
    result_block = data.get("result", data)
    payloads = result_block.get("payloads", [])
    text = "\n".join(p.get("text", "") for p in payloads if p.get("text")).strip()

    # Token usage
    usage: dict = {}
    meta = result_block.get("meta", {})
    agent_meta = meta.get("agentMeta", {})
    for key in ("usage", "lastCallUsage"):
        if key in agent_meta:
            usage = agent_meta[key]
            break

    return text or raw.strip(), usage


def send_via_smtp(subject: str, body: str) -> None:
    """Send *body* as a plain-text email from GMAIL_SENDER to GMAIL_RECEIVER."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = GMAIL_RECEIVER
    msg.attach(MIMEText(body, "plain"))

    # Use certifi bundle if available, otherwise fall back to system default.
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.ehlo()
        s.starttls(context=ctx)
        s.login(GMAIL_SENDER, GMAIL_PASSWORD)
        s.sendmail(GMAIL_SENDER, GMAIL_RECEIVER, msg.as_string())


def extract_subject(text: str, fallback: str) -> str:
    """Pull the Subject: line out of a composed email, or return fallback."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("subject:"):
            return stripped[len("subject:"):].strip()
    return fallback


def build_prompt(task: Task) -> str:
    """Build a single-turn prompt that embeds both context and instruction."""
    ctx_json = json.dumps(task.context, indent=2, ensure_ascii=False)
    return (
        f"You are an AI agent completing a benchmarked email task.\n\n"
        f"CONTEXT (JSON):\n{ctx_json}\n\n"
        f"TASK INSTRUCTION:\n{task.instruction}\n\n"
        f"Complete the task exactly as specified. "
        f"For the FROM/TO fields use the email addresses provided in the context. "
        f"Output only the composed email(s) — no extra commentary."
    )


async def evaluate(task: Task, response_text: str, error: str | None) -> dict:
    """Run the task's rubric/composite evaluator and return the score dict."""
    reg = get_evaluator_registry()
    evaluator_name = task.evaluation.evaluator
    if evaluator_name not in reg:
        return {"overall": 0.0, "note": f"evaluator '{evaluator_name}' not found"}

    agent_response = AgentResponse(output=response_text, error=error)
    score = await reg[evaluator_name].evaluate(task, agent_response, task.evaluation.config)
    return {
        "overall":      round(score.overall      * 100, 1),
        "correctness":  round(score.correctness  * 100, 1),
        "completeness": round(score.completeness * 100, 1),
        "efficiency":   round(score.efficiency   * 100, 1),
        "robustness":   round(score.robustness   * 100, 1),
    }


# ── main ──────────────────────────────────────────────────────────────────────

async def main() -> int:
    # Load builtin tasks + openclaw-specific tasks
    registry = TaskRegistry()
    openclaw_dir = ROOT / "tasks" / "openclaw"
    if openclaw_dir.is_dir():
        registry.add_directory(openclaw_dir)

    email_tasks = [
        t for t in registry.list_all()
        if t.category == TaskCategory.EMAIL
    ]

    print(f"\n{SEPARATOR}")
    print("ClawArena — Email Task Run")
    print(f"  Sender  : {GMAIL_SENDER}")
    print(f"  Receiver: {GMAIL_RECEIVER}")
    print(f"  Tasks   : {len(email_tasks)}")
    print(SEPARATOR)

    records: list[dict] = []

    for idx, task in enumerate(email_tasks, 1):
        print(f"\n[{idx}/{len(email_tasks)}] {task.name}")
        print(f"  id         : {task.id}")
        print(f"  difficulty : {task.difficulty.value}")
        print(f"  timeout    : {task.timeout_seconds}s")

        prompt = build_prompt(task)
        response_text = ""
        error: str | None = None
        usage: dict = {}

        # ── Step 1: call agent ────────────────────────────────────────────
        print("  agent      : ", end="", flush=True)
        try:
            response_text, usage = call_openclaw_agent(
                prompt, timeout=task.timeout_seconds
            )
            tok_in  = usage.get("input",  "?")
            tok_out = usage.get("output", "?")
            print(f"OK  (in={tok_in} out={tok_out} tokens)")
        except subprocess.TimeoutExpired:
            error = "timeout"
            print("TIMEOUT")
        except Exception as exc:
            error = str(exc)
            print(f"ERROR: {exc}")

        # ── Step 2: send email ────────────────────────────────────────────
        sent = False
        subject = extract_subject(response_text, f"[ClawArena] {task.name}")
        if response_text and not error:
            print(f"  sending    : ", end="", flush=True)
            try:
                send_via_smtp(subject, response_text)
                sent = True
                print(f"OK → {GMAIL_RECEIVER}")
            except Exception as exc:
                print(f"SMTP ERROR: {exc}")
                error = str(exc)

        # ── Step 3: evaluate ──────────────────────────────────────────────
        scores = await evaluate(task, response_text, error)
        print(f"  score      : {scores['overall']:.1f}%  "
              f"(correctness={scores['correctness']:.0f}  "
              f"completeness={scores['completeness']:.0f}  "
              f"efficiency={scores['efficiency']:.0f}  "
              f"robustness={scores['robustness']:.0f})")

        # ── Step 4: preview ───────────────────────────────────────────────
        if response_text:
            preview = " ".join(response_text.split())[:180]
            print(f"  preview    : {preview}…")

        records.append({
            "task_id":   task.id,
            "name":      task.name,
            "sent":      sent,
            "subject":   subject,
            "score":     scores["overall"],
            "scores":    scores,
            "error":     error,
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    sent_count  = sum(1 for r in records if r["sent"])
    fail_count  = sum(1 for r in records if r["error"])
    avg_score   = sum(r["score"] for r in records) / len(records) if records else 0

    print(f"\n{SEPARATOR}")
    print("RESULTS SUMMARY")
    print(SEPARATOR)
    print(f"  Emails sent : {sent_count}/{len(records)}")
    print(f"  Failures    : {fail_count}")
    print(f"  Avg score   : {avg_score:.1f}%")
    print()

    col = "{:<45} {:>8} {:>6}"
    print(col.format("Task", "Score", "Sent"))
    print(col.format("─" * 45, "─" * 8, "─" * 6))
    for r in records:
        icon = "✓" if r["sent"] else ("✗" if r["error"] else "─")
        print(col.format(r["task_id"][:45], f"{r['score']:.1f}%", icon))

    print(SEPARATOR)
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
