#!/usr/bin/env python3
"""
RISK-X Synthetic Transaction Dataset Generator
==============================================
Generates a realistic, strictly chronological payment transaction dataset containing
both legitimate payments (with diverse real-world edge cases) and suspicious
fraud scenarios (anomalous amounts, velocity spikes, account takeovers, cross-account
device sharing, geographic/time anomalies, and failed payment bursts).

All exported identifiers (transaction_id, customer_id, merchant_id, device_id,
ip_address, location) are strictly opaque and contain zero semantic label leakage.

Usage:
    python data/generate_dataset.py --n 50000 --seed 42 --output data/raw/transactions.csv
"""

import argparse
import datetime
import math
import os
import random
import sys
from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple

import pandas as pd
import numpy as np


# ==============================================================================
# 1. CONSTANTS & REFERENCE DATA
# ==============================================================================

DOMESTIC_CITIES = [
    "Mumbai", "Bengaluru", "Delhi NCR", "Hyderabad", "Pune",
    "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Goa",
    "Chandigarh", "Kochi", "Lucknow", "Indore", "Surat"
]

INTERNATIONAL_CITIES = [
    "Dubai", "Singapore", "London", "Bangkok", "Kuala Lumpur", "Toronto"
]

ALL_LOCATIONS = DOMESTIC_CITIES + INTERNATIONAL_CITIES

PAYMENT_METHODS = ["upi", "card", "netbanking", "wallet"]

MERCHANT_CATEGORIES = {
    "grocery": {"avg_ticket": 650, "std_ticket": 350},
    "food_dining": {"avg_ticket": 450, "std_ticket": 250},
    "electronics": {"avg_ticket": 14000, "std_ticket": 8000},
    "travel": {"avg_ticket": 7500, "std_ticket": 4500},
    "luxury": {"avg_ticket": 32000, "std_ticket": 15000},
    "streaming_digital": {"avg_ticket": 299, "std_ticket": 150},
    "pharmacy": {"avg_ticket": 550, "std_ticket": 300},
    "utilities": {"avg_ticket": 1800, "std_ticket": 900},
    "crypto_p2p": {"avg_ticket": 25000, "std_ticket": 12000},
}

IP_PREFIX_POOLS = [
    "103.21.", "103.85.", "122.160.", "182.72.", "49.204.",
    "157.34.", "157.48.", "106.210.", "223.233.", "47.247.",
    "185.220.", "194.26.", "45.154.", "91.240.", "178.175."
]


# ==============================================================================
# 2. PROFILE DEFINITIONS
# ==============================================================================

class CustomerProfile:
    def __init__(self, customer_id: str, rng: random.Random, base_time: datetime.datetime):
        self.customer_id = customer_id
        
        # Account registration age (10 to 1200 days before simulation start)
        self.account_created_at = base_time - datetime.timedelta(
            days=rng.randint(10, 1200),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59)
        )
        
        # Customer Persona
        persona_type = rng.choices(
            ["micro_spender", "regular_shopper", "high_volume", "affluent", "night_owl", "budget_student"],
            weights=[0.25, 0.40, 0.12, 0.08, 0.08, 0.07],
            k=1
        )[0]
        
        self.persona = persona_type
        if persona_type == "micro_spender":
            self.base_avg_amount = rng.uniform(150, 450)
            self.active_hours = set(range(8, 23))
            self.payment_pref = {"upi": 0.75, "wallet": 0.15, "card": 0.08, "netbanking": 0.02}
            self.activity_multiplier = 1.0
        elif persona_type == "regular_shopper":
            self.base_avg_amount = rng.uniform(800, 2400)
            self.active_hours = set(range(8, 23))
            self.payment_pref = {"upi": 0.55, "card": 0.30, "netbanking": 0.10, "wallet": 0.05}
            self.activity_multiplier = 1.2
        elif persona_type == "high_volume":
            self.base_avg_amount = rng.uniform(3500, 12000)
            self.active_hours = set(range(8, 21))
            self.payment_pref = {"card": 0.50, "netbanking": 0.35, "upi": 0.15, "wallet": 0.00}
            self.activity_multiplier = 2.0
        elif persona_type == "affluent":
            self.base_avg_amount = rng.uniform(12000, 40000)
            self.active_hours = set(range(9, 23))
            self.payment_pref = {"card": 0.65, "netbanking": 0.25, "upi": 0.10, "wallet": 0.00}
            self.activity_multiplier = 0.7
        elif persona_type == "night_owl":
            self.base_avg_amount = rng.uniform(400, 2000)
            self.active_hours = set([18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 12, 13, 14])
            self.payment_pref = {"upi": 0.60, "card": 0.30, "wallet": 0.08, "netbanking": 0.02}
            self.activity_multiplier = 0.9
        else:  # budget_student
            self.base_avg_amount = rng.uniform(60, 250)
            self.active_hours = set(range(9, 24)).union({0, 1})
            self.payment_pref = {"upi": 0.85, "wallet": 0.12, "card": 0.03, "netbanking": 0.00}
            self.activity_multiplier = 1.3

        # Locations (Primary and secondary)
        primary_city = rng.choice(DOMESTIC_CITIES)
        other_cities = [c for c in DOMESTIC_CITIES if c != primary_city]
        secondary_city = rng.choice(other_cities)
        self.normal_locations = {primary_city: 0.90, secondary_city: 0.10}
        
        # Primary & Secondary Devices (Opaque IDs strictly)
        self.primary_device = f"dev_{rng.randint(10000, 99999)}"
        self.secondary_device = f"dev_{rng.randint(10000, 99999)}" if rng.random() < 0.35 else None
        
        # IP prefixes (Standard telecom & broadband prefixes)
        self.home_ip_prefix = rng.choice(IP_PREFIX_POOLS[:5])
        self.mobile_ip_prefix = rng.choice(IP_PREFIX_POOLS[5:10])
        
        # Historical refund base
        self.refund_count = rng.choices([0, 1, 2, 3, 4], weights=[0.82, 0.12, 0.04, 0.015, 0.005], k=1)[0]


class MerchantProfile:
    def __init__(self, merchant_id: str, rng: random.Random):
        self.merchant_id = merchant_id
        self.category = rng.choice(list(MERCHANT_CATEGORIES.keys()))
        self.info = MERCHANT_CATEGORIES[self.category]
        self.city = rng.choice(DOMESTIC_CITIES) if rng.random() < 0.6 else "Pan-India / Online"


# ==============================================================================
# 3. CHRONOLOGICAL TRANSACTION ENGINE
# ==============================================================================

class TransactionGenerator:
    def __init__(
        self,
        n_transactions: int = 50000,
        seed: int = 42,
        suspicious_rate: float = 0.075,
        start_date: datetime.datetime = datetime.datetime(2026, 6, 1, 6, 0, 0)
    ):
        self.n_transactions = n_transactions
        self.seed = seed
        self.suspicious_rate = suspicious_rate
        self.current_time = start_date
        
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        
        # Population sizing
        self.num_customers = max(2000, int(n_transactions / 18))
        self.num_merchants = max(150, int(self.num_customers / 15))
        
        # Initialize Customers & Merchants (Opaque IDs)
        self.customers: List[CustomerProfile] = [
            CustomerProfile(f"cust_{i:05d}", self.rng, self.current_time)
            for i in range(1, self.num_customers + 1)
        ]
        self.customer_map = {c.customer_id: c for c in self.customers}
        
        self.merchants: List[MerchantProfile] = [
            MerchantProfile(f"merch_{i:04d}", self.rng)
            for i in range(1, self.num_merchants + 1)
        ]
        
        # Shared & Fraud-Ring Devices (Strictly Opaque dev_XXXXX IDs)
        self._init_device_pools()
        
        # Chronological Stateful Tracker Structures
        self.customer_tx_times: Dict[str, deque] = defaultdict(deque)
        self.customer_amounts: Dict[str, List[float]] = defaultdict(list)
        self.customer_known_devices: Dict[str, Set[str]] = defaultdict(set)
        self.device_used_by_accounts: Dict[str, Set[str]] = defaultdict(set)
        
        # Pre-populate known devices
        for c in self.customers:
            self.customer_known_devices[c.customer_id].add(c.primary_device)
            self.device_used_by_accounts[c.primary_device].add(c.customer_id)
            if c.secondary_device:
                self.customer_known_devices[c.customer_id].add(c.secondary_device)
                self.device_used_by_accounts[c.secondary_device].add(c.customer_id)

    def _init_device_pools(self):
        """Create shared household devices and fraud ring devices using completely opaque IDs."""
        # 1. Family / shared household devices (legitimate sharing: 2-3 members, opaque IDs)
        num_family_devices = int(self.num_customers * 0.04)
        self.family_devices: List[str] = [
            f"dev_{self.rng.randint(10000, 99999)}" for _ in range(num_family_devices)
        ]
        for fam_dev in self.family_devices:
            shared_custs = self.rng.sample(self.customers, k=self.rng.randint(2, 3))
            for c in shared_custs:
                c.primary_device = fam_dev
        
        # 2. Fraud Ring Devices (opaque dev_XXXXX IDs shared across multiple victims in Scenario D)
        self.fraud_ring_devices: List[str] = [
            f"dev_{self.rng.randint(10000, 99999)}" for _ in range(30)
        ]

    def generate(self) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Generate transactions in strict chronological order and return dataframe + scenario counts."""
        transactions = []
        txn_counter = 1
        
        # Mutually exclusive primary scenarios
        scenario_types = [
            "A: Amount Anomaly",
            "B: Velocity Spike",
            "C: New Device Takeover",
            "D: Cross-Account Device Reuse",
            "E: Geographic/Time Anomaly",
            "F: Failed Payment Burst"
        ]
        scenario_weights = [0.22, 0.22, 0.15, 0.15, 0.14, 0.12]
        
        primary_scenario_counts = {scen: 0 for scen in scenario_types}
        
        target_suspicious_txns = int(self.n_transactions * self.suspicious_rate)
        suspicious_generated = 0
        
        while len(transactions) < self.n_transactions:
            # Advance platform time strictly forward (1 to 90 seconds)
            hour = self.current_time.hour
            if 0 <= hour <= 5:
                delta_sec = float(self.np_rng.exponential(75)) + 10
            else:
                delta_sec = float(self.np_rng.exponential(25)) + 1
            
            self.current_time += datetime.timedelta(seconds=delta_sec)
            
            # Decide if this transaction event is legitimate or suspicious
            remaining_slots = self.n_transactions - len(transactions)
            remaining_susp = target_suspicious_txns - suspicious_generated
            
            if remaining_susp > 0 and remaining_slots > 0:
                p_susp = max(0.01, min(0.15, (remaining_susp / remaining_slots) * 0.75))
                is_suspicious = (self.rng.random() < p_susp)
            else:
                is_suspicious = False
            
            # Select Customer
            active_hour = self.current_time.hour
            weights = []
            for c in self.customers:
                w = c.activity_multiplier
                if active_hour in c.active_hours:
                    w *= 3.0
                weights.append(w)
                
            customer = self.rng.choices(self.customers, weights=weights, k=1)[0]
            
            if is_suspicious:
                scenario = self.rng.choices(scenario_types, weights=scenario_weights, k=1)[0]
                records = self._generate_suspicious_scenario(txn_counter, customer, scenario)
            else:
                records = [self._generate_legitimate_event(txn_counter, customer)]
                
            for rec in records:
                if len(transactions) < self.n_transactions:
                    transactions.append(rec)
                    if rec["label"] == 1:
                        suspicious_generated += 1
                        # Track mutually exclusive primary scenario
                        primary_scen = rec["_primary_scenario"]
                        primary_scenario_counts[primary_scen] += 1
                    txn_counter += 1
        
        df = pd.DataFrame(transactions)
        
        # Drop internal tracking metadata from exported dataframe
        if "_primary_scenario" in df.columns:
            df = df.drop(columns=["_primary_scenario"])
            
        return df, primary_scenario_counts

    def _generate_legitimate_event(self, txn_id_num: int, customer: CustomerProfile) -> Dict[str, Any]:
        """Generate a realistic legitimate payment event with realistic edge cases."""
        edge_case = self.rng.choices(
            ["standard", "high_amount_purchase", "new_device_upgrade", "travel_location", "rapid_micro_tx", "failed_pin_retry", "corporate_vpn"],
            weights=[0.79, 0.05, 0.03, 0.04, 0.03, 0.03, 0.03],
            k=1
        )[0]
        
        merchant = self.rng.choice(self.merchants)
        
        # 1. Amount
        if edge_case == "high_amount_purchase":
            # Legitimate large purchase (e.g. flights, festival electronics)
            amount = round(customer.base_avg_amount * self.rng.uniform(3.5, 6.5) + self.rng.uniform(1000, 4000), 2)
        elif edge_case == "rapid_micro_tx":
            # Small coffee / tip
            amount = round(self.rng.uniform(25, 180), 2)
        else:
            # Natural lognormal / gamma variation
            raw_amt = float(self.np_rng.gamma(shape=4.0, scale=max(10, customer.base_avg_amount / 4.0)))
            amount = round(float(np.clip(raw_amt, 15.0, customer.base_avg_amount * 3.5)), 2)
            
        # 2. Location
        if edge_case == "travel_location":
            # Legitimate travel / holiday (e.g. Goa, Jaipur, or international hub like Dubai)
            location = self.rng.choice([c for c in ALL_LOCATIONS if c not in customer.normal_locations])
        else:
            locs = list(customer.normal_locations.keys())
            loc_probs = list(customer.normal_locations.values())
            location = self.rng.choices(locs, weights=loc_probs, k=1)[0]
            
        # 3. Device (Opaque format dev_XXXXX)
        if edge_case == "new_device_upgrade":
            # Phone upgrade
            device_id = f"dev_{self.rng.randint(10000, 99999)}"
        else:
            device_id = customer.primary_device
            if customer.secondary_device and self.rng.random() < 0.25:
                device_id = customer.secondary_device
                
        # 4. IP (Opaque standard IPv4 addresses)
        if edge_case == "corporate_vpn":
            ip_prefix = self.rng.choice(IP_PREFIX_POOLS[10:])
        elif edge_case == "travel_location":
            ip_prefix = self.rng.choice(IP_PREFIX_POOLS[5:10])
        else:
            ip_prefix = customer.home_ip_prefix if self.rng.random() < 0.7 else customer.mobile_ip_prefix
        ip_address = f"{ip_prefix}{self.rng.randint(1, 254)}.{self.rng.randint(1, 254)}"
        
        # 5. Payment Method
        methods = list(customer.payment_pref.keys())
        probs = list(customer.payment_pref.values())
        payment_method = self.rng.choices(methods, weights=probs, k=1)[0]
        
        # 6. Failed Attempts
        failed_attempts = self.rng.choice([1, 2]) if edge_case == "failed_pin_retry" else 0
        
        return self._build_record(
            txn_id_num=txn_id_num,
            customer=customer,
            merchant=merchant,
            amount=amount,
            tx_time=self.current_time,
            device_id=device_id,
            ip_address=ip_address,
            location=location,
            payment_method=payment_method,
            failed_attempts=failed_attempts,
            label=0,
            primary_scenario="None (Legitimate)"
        )

    def _generate_suspicious_scenario(
        self, txn_id_num: int, customer: CustomerProfile, scenario: str
    ) -> List[Dict[str, Any]]:
        """Generate suspicious transaction(s) with mutually exclusive primary scenario tracking."""
        records = []
        merchant = self.rng.choice(self.merchants)
        
        if scenario == "A: Amount Anomaly":
            multiplier = self.rng.uniform(8.0, 20.0)
            amount = round(customer.base_avg_amount * multiplier + self.rng.uniform(5000, 20000), 2)
            records.append(self._build_record(
                txn_id_num=txn_id_num,
                customer=customer,
                merchant=merchant,
                amount=amount,
                tx_time=self.current_time,
                device_id=customer.primary_device,
                ip_address=f"{customer.home_ip_prefix}{self.rng.randint(1, 254)}.{self.rng.randint(1, 254)}",
                location=list(customer.normal_locations.keys())[0],
                payment_method="card" if customer.payment_pref.get("card", 0) > 0.1 else "netbanking",
                failed_attempts=0,
                label=1,
                primary_scenario="A: Amount Anomaly"
            ))
            
        elif scenario == "B: Velocity Spike":
            burst_size = self.rng.randint(3, 5)
            for b in range(burst_size):
                if b > 0:
                    self.current_time += datetime.timedelta(seconds=self.rng.randint(15, 60))
                b_amount = round(self.rng.uniform(800, 3200), 2)
                records.append(self._build_record(
                    txn_id_num=txn_id_num + b,
                    customer=customer,
                    merchant=self.rng.choice(self.merchants),
                    amount=b_amount,
                    tx_time=self.current_time,
                    device_id=customer.primary_device,
                    ip_address=f"{customer.mobile_ip_prefix}{self.rng.randint(1, 254)}.{self.rng.randint(1, 254)}",
                    location=list(customer.normal_locations.keys())[0],
                    payment_method="card",
                    failed_attempts=0,
                    label=1,
                    primary_scenario="B: Velocity Spike"
                ))
                
        elif scenario == "C: New Device Takeover":
            # Opaque new device ID
            new_device = f"dev_{self.rng.randint(10000, 99999)}"
            ip_prefix = self.rng.choice(IP_PREFIX_POOLS[10:])
            ip_address = f"{ip_prefix}{self.rng.randint(1, 254)}.{self.rng.randint(1, 254)}"
            amount = round(customer.base_avg_amount * self.rng.uniform(3.5, 8.5), 2)
            records.append(self._build_record(
                txn_id_num=txn_id_num,
                customer=customer,
                merchant=merchant,
                amount=amount,
                tx_time=self.current_time,
                device_id=new_device,
                ip_address=ip_address,
                location=self.rng.choice(DOMESTIC_CITIES),
                payment_method="netbanking",
                failed_attempts=1,
                label=1,
                primary_scenario="C: New Device Takeover"
            ))
            
        elif scenario == "D: Cross-Account Device Reuse":
            # Opaque device shared across multiple accounts
            shared_dev = self.rng.choice(self.fraud_ring_devices)
            ip_prefix = self.rng.choice(IP_PREFIX_POOLS[10:])
            ip_address = f"{ip_prefix}{self.rng.randint(1, 254)}.{self.rng.randint(1, 254)}"
            amount = round(customer.base_avg_amount * self.rng.uniform(2.0, 5.5), 2)
            records.append(self._build_record(
                txn_id_num=txn_id_num,
                customer=customer,
                merchant=merchant,
                amount=amount,
                tx_time=self.current_time,
                device_id=shared_dev,
                ip_address=ip_address,
                location="Delhi NCR",
                payment_method="card",
                failed_attempts=0,
                label=1,
                primary_scenario="D: Cross-Account Device Reuse"
            ))
            
        elif scenario == "E: Geographic/Time Anomaly":
            ip_prefix = self.rng.choice(IP_PREFIX_POOLS[10:])
            ip_address = f"{ip_prefix}{self.rng.randint(1, 254)}.{self.rng.randint(1, 254)}"
            susp_location = self.rng.choice(INTERNATIONAL_CITIES)
            amount = round(customer.base_avg_amount * self.rng.uniform(2.5, 7.0), 2)
            records.append(self._build_record(
                txn_id_num=txn_id_num,
                customer=customer,
                merchant=merchant,
                amount=amount,
                tx_time=self.current_time,
                device_id=customer.primary_device,
                ip_address=ip_address,
                location=susp_location,
                payment_method="card",
                failed_attempts=0,
                label=1,
                primary_scenario="E: Geographic/Time Anomaly"
            ))
            
        else:  # F: Failed Payment Burst
            failed_attempts = self.rng.choice([3, 4, 5])
            amount = round(customer.base_avg_amount * self.rng.uniform(1.8, 4.5), 2)
            records.append(self._build_record(
                txn_id_num=txn_id_num,
                customer=customer,
                merchant=merchant,
                amount=amount,
                tx_time=self.current_time,
                device_id=customer.primary_device,
                ip_address=f"{customer.mobile_ip_prefix}{self.rng.randint(1, 254)}.{self.rng.randint(1, 254)}",
                location=list(customer.normal_locations.keys())[0],
                payment_method="card",
                failed_attempts=failed_attempts,
                label=1,
                primary_scenario="F: Failed Payment Burst"
            ))

        return records

    def _build_record(
        self,
        txn_id_num: int,
        customer: CustomerProfile,
        merchant: MerchantProfile,
        amount: float,
        tx_time: datetime.datetime,
        device_id: str,
        ip_address: str,
        location: str,
        payment_method: str,
        failed_attempts: int,
        label: int,
        primary_scenario: str
    ) -> Dict[str, Any]:
        """Statefully compute features and build a validated transaction row."""
        cid = customer.customer_id
        
        # 1. Account age days at transaction time
        account_age_days = max(1, (tx_time - customer.account_created_at).days)
        
        # 2. Previous transaction count (strictly historical)
        prev_count = len(self.customer_amounts[cid])
        
        # 3. Customer historical average amount (or baseline profile amount if first txn)
        if prev_count > 0:
            cust_avg = round(float(np.mean(self.customer_amounts[cid])), 2)
        else:
            cust_avg = round(float(customer.base_avg_amount), 2)
            
        # 4. Rolling velocity calculations (strictly prior to current transaction)
        ten_min_ago = tx_time - datetime.timedelta(minutes=10)
        one_hr_ago = tx_time - datetime.timedelta(hours=1)
        
        times_queue = self.customer_tx_times[cid]
        while times_queue and times_queue[0] < one_hr_ago:
            times_queue.popleft()
            
        tx_last_10m = sum(1 for t in times_queue if t >= ten_min_ago)
        tx_last_1h = len(times_queue)
        
        # 5. Device account count (distinct accounts using device up to current time)
        dev_accounts = self.device_used_by_accounts[device_id]
        dev_account_count = len(dev_accounts | {cid})
        
        # 6. Flag: is_new_device for this customer
        is_new_device = 1 if device_id not in self.customer_known_devices[cid] else 0
        
        # 7. Flag: is_unusual_time
        is_unusual_time = 1 if tx_time.hour not in customer.active_hours else 0
        
        # 8. Flag: is_unusual_location
        is_unusual_location = 1 if location not in customer.normal_locations else 0
        
        # Ensure positive amount strictly
        final_amount = max(1.0, amount)
        
        # Update Stateful Memory
        self.customer_tx_times[cid].append(tx_time)
        self.customer_amounts[cid].append(final_amount)
        self.customer_known_devices[cid].add(device_id)
        self.device_used_by_accounts[device_id].add(cid)
        
        return {
            "transaction_id": f"txn_{txn_id_num:07d}",
            "customer_id": cid,
            "merchant_id": merchant.merchant_id,
            "amount": final_amount,
            "timestamp": tx_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "device_id": device_id,
            "ip_address": ip_address,
            "location": location,
            "payment_method": payment_method,
            "account_age_days": account_age_days,
            "previous_transaction_count": prev_count,
            "failed_attempts": failed_attempts,
            "refund_count": customer.refund_count,
            "customer_avg_amount": cust_avg,
            "transactions_last_10min": tx_last_10m,
            "transactions_last_1hr": tx_last_1h,
            "device_account_count": dev_account_count,
            "is_new_device": is_new_device,
            "is_unusual_time": is_unusual_time,
            "is_unusual_location": is_unusual_location,
            "label": label,
            "_primary_scenario": primary_scenario
        }


# ==============================================================================
# 4. VALIDATION & QUALITY AUDIT
# ==============================================================================

def validate_dataset(df: pd.DataFrame, primary_scenario_counts: Dict[str, int]) -> Dict[str, Any]:
    """Execute quality checks and assert dataset integrity."""
    required_cols = [
        "transaction_id", "customer_id", "merchant_id", "amount",
        "timestamp", "device_id", "ip_address", "location",
        "payment_method", "account_age_days", "previous_transaction_count",
        "failed_attempts", "refund_count", "customer_avg_amount",
        "transactions_last_10min", "transactions_last_1hr",
        "device_account_count", "is_new_device", "is_unusual_time",
        "is_unusual_location", "label"
    ]
    
    # 1. Check required columns
    missing_cols = set(required_cols) - set(df.columns)
    assert not missing_cols, f"Missing required columns: {missing_cols}"
    
    # 2. Check transaction_id uniqueness
    duplicate_ids = int(df["transaction_id"].duplicated().sum())
    assert duplicate_ids == 0, f"Duplicate transaction IDs detected: {duplicate_ids}"
    
    # 3. Check for null values
    null_counts = int(df.isnull().sum().sum())
    assert null_counts == 0, f"Null values detected in dataset: {null_counts}"
    
    # 4. Check impossible negative amounts
    negative_amounts = int((df["amount"] <= 0).sum())
    assert negative_amounts == 0, f"Non-positive transaction amounts found: {negative_amounts}"
    
    # 5. Check valid labels
    invalid_labels = set(df["label"].unique()) - {0, 1}
    assert not invalid_labels, f"Invalid labels found: {invalid_labels}"
    
    # 6. Check chronological timestamp order
    parsed_dates = pd.to_datetime(df["timestamp"])
    is_sorted = parsed_dates.is_monotonic_increasing
    assert is_sorted, "Timestamps are not in monotonic chronological order"
    
    # 7. Check for semantic leakages in device_id
    semantic_leak_devices = df["device_id"].str.contains("fraud|atk|attack|suspicious|risk|bad|fam", case=False).sum()
    assert semantic_leak_devices == 0, f"Semantic keywords found in device_id: {semantic_leak_devices}"
    
    # 8. Check primary scenario counts sum exactly to suspicious count
    total_txns = len(df)
    suspicious_count = int(df["label"].sum())
    legit_count = total_txns - suspicious_count
    suspicious_pct = (suspicious_count / total_txns) * 100
    
    sum_primary = sum(primary_scenario_counts.values())
    assert sum_primary == suspicious_count, (
        f"Primary scenario sum ({sum_primary}) does not match suspicious count ({suspicious_count})"
    )
    
    # Assert suspicious rate is between 5.0% and 10.0%
    assert 5.0 <= suspicious_pct <= 10.0, f"Suspicious rate out of bounds: {suspicious_pct:.2f}%"
    
    return {
        "total_transactions": total_txns,
        "legitimate_transactions": legit_count,
        "suspicious_transactions": suspicious_count,
        "suspicious_percentage": suspicious_pct,
        "unique_customers": int(df["customer_id"].nunique()),
        "unique_merchants": int(df["merchant_id"].nunique()),
        "unique_devices": int(df["device_id"].nunique()),
        "unique_ips": int(df["ip_address"].nunique()),
        "avg_amount": float(df["amount"].mean()),
        "min_amount": float(df["amount"].min()),
        "max_amount": float(df["amount"].max()),
        "date_min": str(df["timestamp"].min()),
        "date_max": str(df["timestamp"].max()),
        "null_values": null_counts,
        "duplicate_ids": duplicate_ids,
        "semantic_leaks": int(semantic_leak_devices),
        "primary_scenario_counts": primary_scenario_counts
    }


def print_report(stats: Dict[str, Any]):
    """Print formatted dataset statistics and scenario breakdowns."""
    print("=" * 70)
    print("              RISK-X DATASET GENERATION & AUDIT REPORT            ")
    print("=" * 70)
    print(f"Total transactions:          {stats['total_transactions']:,}")
    print(f"Legitimate transactions:     {stats['legitimate_transactions']:,}")
    print(f"Suspicious transactions:     {stats['suspicious_transactions']:,}")
    print(f"Suspicious percentage:       {stats['suspicious_percentage']:.2f}%")
    print("-" * 70)
    print(f"Unique customers:            {stats['unique_customers']:,}")
    print(f"Unique merchants:            {stats['unique_merchants']:,}")
    print(f"Unique devices:              {stats['unique_devices']:,}")
    print(f"Unique IPs:                  {stats['unique_ips']:,}")
    print("-" * 70)
    print(f"Average transaction amount:  INR {stats['avg_amount']:,.2f}")
    print(f"Minimum transaction amount:  INR {stats['min_amount']:,.2f}")
    print(f"Maximum transaction amount:  INR {stats['max_amount']:,.2f}")
    print(f"Date range:                  {stats['date_min']} to {stats['date_max']}")
    print("-" * 70)
    print(f"Missing values:              {stats['null_values']}")
    print(f"Duplicate transaction IDs:   {stats['duplicate_ids']}")
    print(f"Semantic keyword leaks:      {stats['semantic_leaks']}")
    print("-" * 70)
    print("PRIMARY SUSPICIOUS SCENARIOS (Mutually Exclusive):")
    total_susp = stats['suspicious_transactions']
    for scen, count in stats['primary_scenario_counts'].items():
        pct = (count / total_susp) * 100 if total_susp > 0 else 0
        print(f"  - {scen:<32} {count:>5,} ({pct:>5.2f}%)")
    print(f"  {'SUM OF SCENARIOS:':<34} {sum(stats['primary_scenario_counts'].values()):>5,} (100.00%)")
    print("-" * 70)
    print("Validation Status:           PASSED (All assertions met)")
    print("=" * 70)


# ==============================================================================
# 5. CLI ENTRYPOINT
# ==============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Generate synthetic payment transactions for RISK-X.")
    parser.add_argument("--n", type=int, default=50000, help="Total number of transactions to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=str, default="data/raw/transactions.csv", help="Output path for CSV.")
    parser.add_argument("--sample-output", type=str, default="data/raw/transactions_sample.csv", help="Sample CSV path.")
    parser.add_argument("--sample-size", type=int, default=1000, help="Number of rows for sample CSV.")
    parser.add_argument("--suspicious-rate", type=float, default=0.075, help="Target fraction of suspicious txns.")
    return parser.parse_args()


def main():
    args = parse_args()
    
    print(f"[*] Initializing RISK-X generator: n={args.n}, seed={args.seed}, target_suspicious_rate={args.suspicious_rate:.1%}")
    generator = TransactionGenerator(
        n_transactions=args.n,
        seed=args.seed,
        suspicious_rate=args.suspicious_rate
    )
    
    print("[*] Simulating customer transactions across time...")
    df, primary_scenarios = generator.generate()
    
    print("[*] Validating dataset integrity...")
    stats = validate_dataset(df, primary_scenarios)
    print_report(stats)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print(f"[*] Saving full dataset to: {args.output}")
    df.to_csv(args.output, index=False)
    
    if args.sample_output and args.sample_size > 0:
        sample_size = min(args.sample_size, len(df))
        print(f"[*] Saving sample dataset ({sample_size} rows) to: {args.sample_output}")
        df.head(sample_size).to_csv(args.sample_output, index=False)
        
    print("[+] Dataset generation complete and verified successfully.")


if __name__ == "__main__":
    main()
