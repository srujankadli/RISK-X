# RISK-X Data Management

This directory manages transaction datasets, synthetic test cases, and preprocessing pipelines.

---

## Directory Structure

```
data/
├── raw/                # Unmodified transaction feeds and raw generated datasets
├── processed/          # Cleaned, normalized, and feature-engineered datasets
└── README.md
```

---

## Planned Transaction Data Schema

In Milestone 2, we will define a Razorpay-compatible transaction schema including:
- `transaction_id`: Unique identifier (e.g., `txn_...`)
- `timestamp`: ISO 8601 UTC timestamp
- `amount`: Payment amount in paise / INR
- `currency`: Default `INR`
- `customer_id`: Unique user identifier
- `merchant_id`: Razorpay merchant identifier
- `payment_method`: `card`, `upi`, `netbanking`, `wallet`
- `card_bin`: First 6 digits of card
- `card_last4`: Last 4 digits of card
- `ip_address`: Client IP address
- `device_fingerprint`: Hash representing device attributes
- `billing_country`: Country of card / account
- `shipping_country`: Country of delivery
- `is_fraud`: Ground truth label for evaluation
