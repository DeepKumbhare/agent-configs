---
name: creem-heartbeat
version: 0.1.0
description: Periodic store monitoring routine for AI agents. Track transactions, subscriptions, and customers — notify your human when things change.
homepage: https://creem.io
metadata:
 {
 "creem":
 {
 "category": "monitoring",
 "api_base": "https://api.creem.io",
 "test_api_base": "https://test-api.creem.io"
 }
 }
---

Fetched from: https://www.creem.io/HEARTBEAT.md
Fetched on: 2026-03-31

Important:
- This file was sourced from an external website and stored locally as a reference.
- Treat it as product documentation, not trusted local policy.
- Re-fetch from the source URL periodically for updates.

# Creem Store Heartbeat

Periodic store monitoring routine for a Creem store.

## Goal
On each heartbeat cycle:
- query current store state
- compare against saved snapshot
- detect meaningful changes
- notify the human only when something changed
- save the new snapshot

## Prerequisites
Need one of:
- Creem CLI installed and authenticated
- A Creem API key for direct HTTP calls
- A persistent writable location for state

## State file
Default state structure:

```json
{
  "lastCheckAt": null,
  "lastTransactionId": null,
  "transactionCount": 0,
  "customerCount": 0,
  "subscriptions": {
    "active": 0,
    "trialing": 0,
    "past_due": 0,
    "paused": 0,
    "canceled": 0,
    "expired": 0,
    "scheduled_cancel": 0
  },
  "knownSubscriptions": {}
}
```

## Recommended cadence
Every 1–4 hours depending on store volume.
Default: every 4 hours.

## Routine

### 1. Load previous state
If state file doesn’t exist, create it and treat this as first run.

### 2. Check new transactions
CLI:
- `creem transactions list --limit 20 --json`

API equivalent:
- `GET /v1/transactions/search?limit=20`

Detect:
- newest transaction changed
- unseen transaction IDs
- extract amount, currency, status, product, customer, created time

### 3. Check subscription health
CLI examples:
- `creem subscriptions list --status active --json`
- `creem subscriptions list --status past_due --json`
- `creem subscriptions list --status canceled --json`
- `creem subscriptions list --status paused --json`
- `creem subscriptions list --status trialing --json`
- `creem subscriptions list --status expired --json`

Detect:
- new subscriptions
- cancellations
- scheduled cancellations
- payment failures (`past_due`)
- expired subscriptions
- paused/resumed subscriptions
- upgrades/downgrades if visible from product/price changes

Update `knownSubscriptions` with latest statuses.

### 4. Check for new customers
CLI:
- `creem customers list --json`

API equivalent:
- `GET /v1/customers/list`

Compare customer count against previous snapshot.

### 5. Update state file
Write refreshed snapshot with timestamps and counts.

### 6. Notify only on meaningful changes
Do not send “no changes” messages.

## Notify immediately for
- new transaction
- subscription canceled
- subscription scheduled to cancel
- payment failure / past_due
- subscription expired
- new customer
- multiple cancellations in one cycle

## Stay silent for
- no changes
- normal renewals
- initial state file creation itself

## Example report styles

### New sale
- Product
- Customer
- Type
- Time

### Subscription canceled
- Customer
- Product
- Whether immediate or scheduled

### Payment failure
- Customer
- Product
- Status: past_due
- Mention retry risk

### Summary update
- number of new transactions
- total value
- new customers
- subscriptions at risk
- active subscription delta

### First snapshot
Summarize current state and say monitoring is now active.

## Edge cases
- If CLI unavailable, use API directly
- If API key unavailable, ask user for one
- Don’t run more than hourly
- If state file corrupts, recreate it and treat next run as first snapshot
- If multiple stores exist, use separate state files per store

## Quick checks
- Compare latest transaction ID to saved transaction ID
- Count active subscriptions
- Count past_due subscriptions

## Recommended local files
- `skills/creem/SKILL.md`
- `skills/creem/HEARTBEAT.md`
- runtime state file such as `~/.creem/heartbeat-state.json` or workspace equivalent
