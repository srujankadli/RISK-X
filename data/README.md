# RISK-X Data Management & Synthetic Dataset Generator

This directory contains the synthetic payment transaction generator and generated transaction datasets used for training and evaluating the RISK-X risk engine.

---

## 1. Directory Structure

```
data/
├── raw/
│   ├── transactions.csv         # Full synthetic dataset (50,000 transactions)
│   ├── transactions_sample.csv  # Development sample (1,000 transactions)
│   └── .gitkeep
├── processed/                   # Reserved for preprocessed & scaled feature matrices
│   └── .gitkeep
├── generate_dataset.py          # Reproducible synthetic transaction generator
└── README.md
```

---

## 2. Dataset Schema (Chronological)

All identifiers (`transaction_id`, `customer_id`, `merchant_id`, `device_id`, `ip_address`, `location`) are strictly opaque and contain zero semantic label leakage.

| Column | Type | Description |
|---|---|---|
| `transaction_id` | String | Unique transaction identifier (`txn_0000001`) |
| `customer_id` | String | Customer identifier (`cust_00001`) |
| `merchant_id` | String | Merchant identifier (`merch_0001`) |
| `amount` | Float | Transaction amount in INR (> 0) |
| `timestamp` | String | ISO 8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`) |
| `device_id` | String | Opaque hardware/browser device fingerprint (`dev_XXXXX`) |
| `ip_address` | String | Client IP address (standard dotted IPv4) |
| `location` | String | City or region of the payment request |
| `payment_method` | String | `upi`, `card`, `netbanking`, or `wallet` |
| `account_age_days` | Integer | Account age in days at the time of transaction |
| `previous_transaction_count`| Integer | Historical transaction count for this customer |
| `failed_attempts` | Integer | Immediate failed attempts prior to this transaction |
| `refund_count` | Integer | Historical refund count for this customer |
| `customer_avg_amount` | Float | Historical average amount for this customer |
| `transactions_last_10min` | Integer | Rolling customer transactions in the prior 10 minutes |
| `transactions_last_1hr` | Integer | Rolling customer transactions in the prior 1 hour |
| `device_account_count` | Integer | Number of distinct customer accounts using this device |
| `is_new_device` | Integer (0/1)| 1 if first time customer has used this device, else 0 |
| `is_unusual_time` | Integer (0/1)| 1 if transaction hour is outside customer active hours, else 0 |
| `is_unusual_location` | Integer (0/1)| 1 if location is outside customer regular cities, else 0 |
| `label` | Integer (0/1)| `0` = Legitimate, `1` = Suspicious |

---

## 3. Synthetic Fraud Scenarios (Mutually Exclusive Primary Attribution)

The generator injects 6 core fraud attack types:
- **Scenario A — Amount Anomaly**: Sudden massive spike in transaction amount (8x - 20x historical average).
- **Scenario B — Velocity Spike**: Rapid transaction bursts (card testing / rapid account draining) within 10 minutes.
- **Scenario C — New Device Takeover**: Account takeover originating from an unobserved device over datacenter/VPN IP.
- **Scenario D — Cross-Account Device Reuse**: Multi-account fraud ring sharing compromised devices across multiple victim accounts.
- **Scenario E — Geographic / Time Anomaly**: Suspicious transactions originating from foreign/high-risk proxy locations during atypical hours.
- **Scenario F — Failed Payment Burst**: Multiple failed PIN/OTP attempts (3 to 5) before a compromised authorization.

---

## 4. Legitimate Edge Cases (Preventing Model Leakage)

To prevent ML models from learning trivial 1-feature rules (e.g. `is_new_device=1 -> fraud`), the generator incorporates diverse legitimate variations:
1. **Legitimate high-ticket purchases**: Normal users purchasing flight tickets or electronics (`label=0`).
2. **Legitimate phone upgrades**: Users accessing from a new device for regular shopping (`label=0`, `is_new_device=1`).
3. **Legitimate travel**: Domestic vacations and international travel on mobile data (`label=0`, `is_unusual_location=1`).
4. **Legitimate quick bursts**: Consecutive food delivery orders or tips (`label=0`, `transactions_last_10min > 1`).
5. **Legitimate retry after failed PIN**: 1-2 mistyped OTPs before successful checkout (`label=0`, `failed_attempts=1 or 2`).
6. **Legitimate shared household devices**: Family iPads/PCs shared across 2-3 accounts (`label=0`, `device_account_count=2 or 3`).
7. **Legitimate corporate VPN usage**: Legitimate remote workers and employees transacting over VPN ranges (`label=0`).

---

## 5. CLI Usage & Reproducibility

```bash
# Generate default 50,000 transactions with seed 42
python data/generate_dataset.py --n 50000 --seed 42

# Generate custom dataset size and output path
python data/generate_dataset.py --n 100000 --seed 123 --output data/raw/transactions_100k.csv --suspicious-rate 0.08
```
