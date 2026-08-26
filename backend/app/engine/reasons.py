"""
RISK-X Explainability & Risk Reason Extraction Module
=====================================================
Generates concise, human-interpretable, evidence-backed risk reasons derived
strictly from observable transaction-time features and behavioral signals.
"""

from typing import Any, Dict, List, Union


def extract_risk_reasons(transaction_data: Union[Dict[str, Any], Any]) -> List[str]:
    """
    Extracts human-readable risk signals from observable transaction attributes.

    All generated reasons are strictly descriptive of observable state at time t
    and avoid causal over-claims or raw model internal details.

    Args:
        transaction_data: Dictionary or object containing transaction attributes:
            - amount (float)
            - customer_avg_amount (float)
            - transactions_last_10min (int)
            - transactions_last_1hr (int)
            - failed_attempts (int)
            - is_new_device (int/bool)
            - device_account_count (int)
            - is_unusual_location (int/bool)
            - is_unusual_time (int/bool)

    Returns:
        List[str]: List of human-readable risk reason strings, prefixed with 'Risk signal: '.
                   Returns an empty list if no elevated risk signals are observed.
    """
    if hasattr(transaction_data, "model_dump"):
        data = transaction_data.model_dump()
    elif hasattr(transaction_data, "__dict__") and not isinstance(transaction_data, dict):
        data = transaction_data.__dict__
    elif isinstance(transaction_data, dict):
        data = transaction_data
    else:
        data = {}

    reasons: List[str] = []

    # 1. Amount Anomaly Check
    amount = float(data.get("amount", 0.0) or 0.0)
    customer_avg = float(data.get("customer_avg_amount", 0.0) or 0.0)
    if customer_avg > 0 and amount >= (3.0 * customer_avg):
        ratio = amount / customer_avg
        reasons.append(
            f"Risk signal: transaction amount is significantly above customer historical average ({ratio:.1f}x higher)."
        )

    # 2. Velocity Spike Check
    tx_10min = int(data.get("transactions_last_10min", 0) or 0)
    tx_1hr = int(data.get("transactions_last_1hr", 0) or 0)
    if tx_10min >= 2:
        reasons.append(
            f"Risk signal: high transaction velocity detected ({tx_10min} payments in the last 10 minutes)."
        )
    elif tx_10min == 1 and tx_1hr >= 3:
        reasons.append(
            f"Risk signal: elevated transaction velocity detected ({tx_1hr} payments in the last hour)."
        )

    # 3. Failed Payment Attempts Check
    failed_attempts = int(data.get("failed_attempts", 0) or 0)
    if failed_attempts >= 2:
        reasons.append(
            f"Risk signal: multiple failed payment attempts detected ({failed_attempts} failed attempts prior to authorization)."
        )
    elif failed_attempts == 1:
        reasons.append(
            "Risk signal: previous failed payment attempt recorded prior to authorization."
        )

    # 4. New / Unrecognized Device Check
    is_new_device = int(data.get("is_new_device", 0) or 0)
    if is_new_device == 1:
        reasons.append(
            "Risk signal: payment initiated from an unrecognized/new device."
        )

    # 5. Multi-Account Device Reuse Check
    device_account_count = int(data.get("device_account_count", 1) or 1)
    if device_account_count >= 2:
        reasons.append(
            f"Risk signal: device is associated with multiple customer accounts ({device_account_count} accounts observed)."
        )

    # 6. Unusual Location Anomaly Check
    is_unusual_location = int(data.get("is_unusual_location", 0) or 0)
    if is_unusual_location == 1:
        reasons.append(
            "Risk signal: unusual transaction location detected outside typical customer operating regions."
        )

    # 7. Unusual Time Anomaly Check
    is_unusual_time = int(data.get("is_unusual_time", 0) or 0)
    if is_unusual_time == 1:
        reasons.append(
            "Risk signal: transaction initiated during atypical customer activity hours."
        )

    return reasons
