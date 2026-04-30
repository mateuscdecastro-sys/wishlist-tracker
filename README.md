# Wishlist Price Tracker

Monitors a private Amazon wishlist hourly and sends a push notification to your phone when any item drops 40%+ in price.

## How it works

- Runs on **GitHub Actions** (free, 24/7, no laptop required)
- Authenticates with Amazon using your browser session cookies
- Sends alerts via **[ntfy.sh](https://ntfy.sh)** — free push notifications to your phone
- Price history is saved in `prices.json` and committed back to this repo after each run

## Setup

See [setup.md](setup.md) for the full step-by-step guide.
