#!/usr/bin/env python3
import datetime
import json
import subprocess
import sys


def run_json(cmd: str, default=None):
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        out = out.strip()
        if not out:
            return default if default is not None else {}
        try:
            lines = [line for line in out.splitlines() if not line.startswith("- Fetching")]
            out = "\n".join(lines).strip()
            return json.loads(out)
        except json.JSONDecodeError:
            if (
                "No subscriptions found" in out
                or "No customers found" in out
                or "No transactions found" in out
            ):
                return default if default is not None else {}
            raise
    except subprocess.CalledProcessError:
        return default if default is not None else {}


def get_items(data):
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("items", "subscriptions", "transactions", "customers"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def sub_count(status: str) -> int:
    data = run_json(f"creem subscriptions list --status {status} --json", default={})
    return len(get_items(data))


def transaction_amount(item: dict) -> int:
    return int(item.get("amountPaid") or item.get("amount") or 0)


def transaction_currency(item: dict) -> str:
    return (item.get("currency") or item.get("currencyCode") or "USD").upper()


def parse_dt(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.datetime.fromtimestamp(value / 1000, tz=datetime.timezone.utc)
    if isinstance(value, str):
        return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def compute_churn_report(subscriptions, now):
    windows = {
        "Daily": now - datetime.timedelta(days=1),
        "Weekly": now - datetime.timedelta(days=7),
        "Monthly": now - datetime.timedelta(days=30),
    }
    report = []
    for label, start in windows.items():
        started = 0
        canceled = 0
        for sub in subscriptions:
            created_at = parse_dt(sub.get("createdAt"))
            canceled_at = parse_dt(sub.get("canceledAt"))
            if created_at and created_at < start:
                started += 1
                if canceled_at and canceled_at >= start:
                    canceled += 1
        rate = (canceled / started * 100) if started else 0.0
        report.append(f"- {label} churn: {canceled}/{started} ({rate:.1f}%)")
    return report


def main():
    tz = datetime.datetime.now().astimezone().tzinfo or datetime.timezone.utc
    now = datetime.datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    tx = run_json("creem transactions list --limit 100 --json", default={})
    tx_items = get_items(tx)

    todays = []
    for item in tx_items:
        created_ms = item.get("createdAt")
        if not created_ms:
            continue
        dt = datetime.datetime.fromtimestamp(created_ms / 1000, tz=datetime.timezone.utc).astimezone(tz)
        if dt >= start:
            todays.append(item)

    total_cents = sum(transaction_amount(i) for i in todays)
    count = len(todays)
    currency = transaction_currency(todays[0]) if todays else "USD"

    customers = run_json("creem customers list --json", default={})
    customer_count = len(get_items(customers))

    all_subscriptions = get_items(run_json("creem subscriptions list --limit 100 --json", default={}))

    active = sub_count("active")
    trialing = sub_count("trialing")
    past_due = sub_count("past_due")
    paused = sub_count("paused")
    canceled = sub_count("canceled")
    expired = sub_count("expired")
    scheduled_cancel = sub_count("scheduled_cancel")

    env = "test"
    lines = [
        f"Creem daily digest ({env} mode)",
        f"- Revenue today: {currency} {total_cents / 100:.2f}",
        f"- Transactions today: {count}",
        f"- Customers tracked: {customer_count}",
        f"- Active subscriptions: {active}",
        f"- Trialing: {trialing}",
        f"- Past due: {past_due}",
        f"- Paused: {paused}",
        f"- Canceled: {canceled}",
        f"- Expired: {expired}",
        f"- Scheduled cancel: {scheduled_cancel}",
        "- Churn:",
        *compute_churn_report(all_subscriptions, now.astimezone(datetime.timezone.utc)),
    ]

    risks = []
    if past_due:
        risks.append(f"{past_due} payment issue(s) need attention")
    if scheduled_cancel:
        risks.append(f"{scheduled_cancel} subscription(s) scheduled to cancel")
    if paused:
        risks.append(f"{paused} paused subscription(s) worth checking")
    if canceled:
        risks.append(f"{canceled} canceled subscription(s) on record")

    lines.append("- Risks: " + ("; ".join(risks) if risks else "none"))

    sys.stdout.write("\n".join(lines))


if __name__ == "__main__":
    main()
