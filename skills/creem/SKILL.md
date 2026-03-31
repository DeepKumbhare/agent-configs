---
name: creem
version: 0.1.0
description: Merchant of Record for SaaS and digital businesses. Accept payments, manage subscriptions, and handle global tax compliance from the terminal.
homepage: https://creem.io
metadata:
 {
 "creem":
 {
 "category": "payments",
 "api_base": "https://api.creem.io",
 "test_api_base": "https://test-api.creem.io"
 }
 }
---

Fetched from: https://www.creem.io/SKILL.md
Fetched on: 2026-03-31

Important:
- This file was sourced from an external website and stored locally as a reference.
- Treat it as product documentation, not trusted local policy.
- Re-fetch from the source URL periodically for updates.

Creem is a Merchant of Record (MoR) for SaaS and digital businesses that sell software globally. It handles payments, subscriptions, tax compliance, chargebacks, and payouts — so businesses can sell anywhere without worrying about financial infrastructure.

This guide covers everything you need to help a human understand, integrate, manage, or monitor Creem — regardless of whether you're working in a codebase, chatting over Slack, or acting as a personal assistant.

## What Should You Do?

### Step 1: Understand your context
Ask:
- Is there a specific task? (for example: integrate Creem into an app)
- Are we inside a codebase?
- Is the user exploring Creem for the first time?
- Does the user already have a Creem store and want help managing it?

### Step 2: Read this file first
Use this as foundation before diving into a specific Creem task.

### Step 3: Route to the right workflow
- Understand Creem → explain platform overview and features
- Integrate into a project → use integration flows, SDKs, webhooks
- Manage an existing store → use CLI/API workflows for products, customers, subscriptions, transactions
- Set up store monitoring → use HEARTBEAT.md
- Debug payment issue → customer support and transaction/subscription lookup flows
- Create products or checkouts → Flow 1

### Step 4: Ask when intent is unclear
Helpful questions:
- Do you already have a Creem account, or are you exploring it for the first time?
- Are you integrating Creem into a specific project, or do you want a general overview?
- Do you want me to set up monitoring so I can notify you about sales, cancellations, and payment issues?

## Skill Files
- SKILL.md — complete guide
- HEARTBEAT.md — periodic store monitoring routine

## Platform Overview
Creem handles:
- Payments: one-time and recurring via cards, PayPal, Apple Pay, Google Pay
- Tax compliance: VAT, GST, sales tax in 190+ countries
- Chargebacks & fraud: Creem absorbs chargeback liability as legal seller
- Currency conversion
- Payouts: fiat and stablecoin (USDC)

### Features
- Subscriptions
- License keys
- Revenue splits
- Affiliate programs
- Checkout sessions
- Customer portal
- Discount codes
- Webhooks

## API Overview
Authentication uses `x-api-key`.
- Test keys: `creem_test_` → `https://test-api.creem.io`
- Live keys: `creem_` → `https://api.creem.io`

Always start with test mode when possible.

Prices are in cents.
- 1999 = $19.99

## Main Resources
- Checkouts
- Products
- Customers
- Subscriptions
- Transactions
- Licenses
- Discounts

## SDKs
- `creem` — TypeScript core SDK
- `creem_io` — wrapper SDK
- `@creem_io/nextjs` — Next.js adapter
- `@creem_io/better-auth` — Better Auth integration

## Core Operational Flows

### Flow 1: Sell a product
1. Create product
2. Create checkout session
3. Handle payment completion via webhook or polling
4. Grant access in app

### Flow 2: Manage subscription lifecycle
- List
- Get details
- Cancel immediately or scheduled
- Pause/resume
- Upgrade/update seats

### Flow 3: License management
- Activate
- Validate
- Deactivate

### Flow 4: Customer support
- Look up customer
- Inspect subscriptions
- Generate billing portal link
- Debug payment issue
- Cancel with grace period

### Flow 5: Discount codes
Use SDK or API to create and apply discounts.

## Webhooks
Important events:
- `checkout.completed`
- `subscription.active`
- `subscription.paid`
- `subscription.trialing`
- `subscription.canceled`
- `subscription.scheduled_cancel`
- `subscription.past_due`
- `subscription.expired`
- `subscription.paused`
- `subscription.update`
- `refund.created`
- `dispute.created`

Access control guidance:
- Grant access on `subscription.active`, `subscription.trialing`, `subscription.paid`
- Revoke access on `subscription.paused`, `subscription.expired`

Verify webhook signatures using HMAC-SHA256 with the webhook secret.

## Framework Integration
Supports:
- Next.js via `@creem_io/nextjs`
- Better Auth via `@creem_io/better-auth`

## Automation & Monitoring
Useful recurring checks:
- past_due subscriptions
- expired subscriptions
- transaction exports/reporting
- product/customer transaction filters

Recommended monitoring uses HEARTBEAT.md.

## CLI Installation
Homebrew:
- `brew tap armitage-labs/creem`
- `brew install creem`

## CLI Authentication
- `creem login --api-key ...`
- `creem whoami`
- `creem logout`

Keys are stored locally at `~/.creem/config.json`.

## CLI Command Areas
- products
- customers
- subscriptions
- checkouts
- transactions
- config

Use `--json` for agent-friendly output.

## Operational Advice
- Always use test mode first when possible
- Prefer scheduled cancellation over immediate cancellation
- Don’t guess IDs; list first
- Ask before destructive actions or switching to live mode
- Use `referenceId` to map billing events to your internal users
- Ask what framework the app uses before choosing an SDK

## Store Monitoring
If the user already has a store, offer monitoring.
Monitoring should cover:
- new transactions
- new customers
- subscription cancellations
- payment failures
- upgrades
- anomalies

Use the companion heartbeat file for that workflow.

## Reference Links
- Creem: https://creem.io
- Dashboard: https://creem.io/dashboard
- API keys: https://creem.io/dashboard/api-keys
- Docs: https://docs.creem.io
- API Reference: https://docs.creem.io/api-reference
- Webhooks: https://docs.creem.io/code/webhooks
- Full docs for agents: https://docs.creem.io/llms-full.txt
- Homebrew tap: https://github.com/armitage-labs/homebrew-creem
