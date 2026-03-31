#!/usr/bin/env python3
import json
import subprocess
import datetime
from pathlib import Path

STATE_PATH = Path("/Users/deepkumbhare/.openclaw/workspace/creem/heartbeat-state.json")

STATUSES = [
    "active",
    "trialing",
    "past_due",
    "paused",
    "canceled",
    "expired",
    "scheduled_cancel",
]


def run_json(cmd: str):
    out = subprocess.check_output(cmd, shell=True, text=True)
    lines = [line for line in out.splitlines() if not line.startswith("- Fetching")]
    return json.loads("\n".join(lines).strip() or "{}")


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


def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {
        "store": {"environment": "test", "source": "creem-cli"},
        "lastCheckAt": None,
        "lastTransactionId": None,
        "transactionCount": 0,
        "customerCount": 0,
        "subscriptions": {s: 0 for s in STATUSES},
        "knownSubscriptions": {},
        "churn": {},
    }


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
        "daily": now - datetime.timedelta(days=1),
        "weekly": now - datetime.timedelta(days=7),
        "monthly": now - datetime.timedelta(days=30),
    }
    report = {}

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
        report[label] = {
            "start_active_estimate": started,
            "canceled": canceled,
            "rate_pct": round(rate, 1),
        }
    return report


def current_snapshot():
    now = datetime.datetime.now(datetime.timezone.utc)
    snap = {
        "store": {
            "environment": "test",
            "source": "creem-cli",
            "initializedAt": now.isoformat(),
        },
        "lastCheckAt": now.isoformat(),
        "lastTransactionId": None,
        "transactionCount": 0,
        "customerCount": 0,
        "subscriptions": {s: 0 for s in STATUSES},
        "knownSubscriptions": {},
        "newTransactions": [],
        "newCustomers": 0,
        "statusChanges": [],
        "churn": {},
    }

    tx = run_json("creem transactions list --limit 20 --json")
    tx_items = get_items(tx)
    snap["lastTransactionId"] = tx_items[0].get("id") if tx_items else None
    snap["transactionCount"] = tx.get("pagination", {}).get("totalRecords", len(tx_items)) if isinstance(tx, dict) else len(tx_items)

    customers = run_json("creem customers list --json")
    cust_items = get_items(customers)
    snap["customerCount"] = len(cust_items)

    all_subs = get_items(run_json("creem subscriptions list --limit 100 --json"))
    snap["churn"] = compute_churn_report(all_subs, now)

    for sub in all_subs:
        status = sub.get("status")
        sid = sub.get("id")
        if status in snap["subscriptions"]:
            snap["subscriptions"][status] += 1
        if sid:
            snap["knownSubscriptions"][sid] = status

    for status in STATUSES:
        if snap["subscriptions"][status]:
            continue
        try:
            data = run_json(f"creem subscriptions list --status {status} --json")
            items = get_items(data)
            snap["subscriptions"][status] = len(items)
            for sub in items:
                sid = sub.get("id")
                if sid:
                    snap["knownSubscriptions"][sid] = sub.get("status", status)
        except Exception:
            pass

    snap["_txItems"] = tx_items
    return snap


def format_churn(churn):
    parts = []
    for label in ("daily", "weekly", "monthly"):
        data = churn.get(label, {})
        parts.append(
            f"{label} churn: {data.get('canceled', 0)}/{data.get('start_active_estimate', 0)} ({data.get('rate_pct', 0):.1f}%)"
        )
    return "; ".join(parts)


def build_message(prev, cur):
    messages = []

    prev_tx = prev.get("lastTransactionId")
    tx_items = cur.get("_txItems", [])
    if tx_items and tx_items[0].get("id") != prev_tx:
        new_items = []
        for item in tx_items:
            if item.get("id") == prev_tx:
                break
            new_items.append(item)
        if new_items:
            total = sum((i.get("amountPaid") or i.get("amount") or 0) for i in new_items) / 100
            messages.append(f"Creem heartbeat update: {len(new_items)} new transaction(s) (${total:.2f} total) in test mode.")

    if cur["customerCount"] > prev.get("customerCount", 0):
        delta = cur["customerCount"] - prev.get("customerCount", 0)
        messages.append(f"{delta} new customer(s) detected in Creem test store.")

    prev_known = prev.get("knownSubscriptions", {})
    cur_known = cur.get("knownSubscriptions", {})
    changes = []
    for sid, status in cur_known.items():
        old = prev_known.get(sid)
        if old and old != status:
            changes.append((sid, old, status))
        elif not old and status in STATUSES:
            changes.append((sid, None, status))

    churn_summary = format_churn(cur.get("churn", {}))

    for sid, old, status in changes:
        if status == "past_due":
            messages.append(f"Payment failed: subscription {sid} is now past_due. Creem will retry automatically. {churn_summary}")
        elif status == "scheduled_cancel":
            messages.append(f"Churn risk: subscription {sid} is scheduled to cancel. {churn_summary}")
        elif status == "expired":
            messages.append(f"Churn confirmed: subscription {sid} expired after failed retries. {churn_summary}")
        elif status == "canceled":
            messages.append(f"Subscription canceled: {sid} is now canceled. {churn_summary}")

    return "\n".join(messages).strip()


def save_state(cur):
    cur = {k: v for k, v in cur.items() if not k.startswith("_")}
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(cur, indent=2))


if __name__ == "__main__":
    prev = load_state()
    cur = current_snapshot()
    message = build_message(prev, cur)
    save_state(cur)
    if message:
        print(message)
