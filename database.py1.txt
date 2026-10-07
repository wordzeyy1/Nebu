import os
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is not set")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY is not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

USER_COLUMNS = (
    "user_id,full_name,email,phone,country,wallet_address,kyc_status,"
    "wallet_balance,affiliate_balance,referrals,referrer_id,first_deposit"
)


def _rows(data):
    return data or []


def _one(data):
    rows = data or []
    return rows[0] if rows else None


def _user_tuple(row):
    if not row:
        return None
    return tuple(row.get(k) for k in (
        "user_id", "full_name", "email", "phone", "country",
        "wallet_address", "kyc_status", "wallet_balance",
        "affiliate_balance", "referrals", "referrer_id", "first_deposit"
    ))


def _deposit_tuple(row):
    return tuple(row.get(k) for k in (
        "id", "user_id", "network", "amount", "crypto_amount", "txid", "status"
    ))


def _refund_tuple(row):
    return tuple(row.get(k) for k in (
        "id", "user_id", "full_name", "investment_date", "profile_id",
        "investment_amount", "cryptocurrency", "exchange_wallet",
        "sender_wallet", "evidence_text", "evidence_file_ids", "status"
    ))


def _kyc_tuple(row):
    return tuple(row.get(k) for k in (
        "id", "user_id", "full_name", "id_document",
        "selfie_document", "status", "submitted_at"
    ))


def _mining_contract_tuple(row):
    return tuple(row.get(k) for k in (
        "id", "user_id", "hash_power", "purchase_price",
        "daily_income", "purchase_date", "last_claim", "status"
    ))


def _withdrawal_tuple(row):
    return tuple(row.get(k) for k in (
        "id", "user_id", "cryptocurrency", "wallet_address",
        "amount", "status", "rejection_reason", "txid",
        "completed_at", "created_at"
    ))


def _wallet_transaction_tuple(row):
    return tuple(row.get(k) for k in (
        "transaction_type", "amount", "reason", "created_at"
    ))


def _parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.now()

    value = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value).replace(tzinfo=None)
    except ValueError:
        return datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")


def create_tables():
    """Tables are created in Supabase SQL Editor, not from the bot."""
    try:
        supabase.table("users").select("user_id").limit(1).execute()
        return True
    except Exception as exc:
        raise RuntimeError(
            f"Supabase connection/table check failed: {exc}"
        ) from exc


# =====================================
# USER FUNCTIONS
# =====================================

def user_exists(user_id):
    result = (
        supabase.table("users")
        .select("user_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return bool(result.data)


def add_user(user_id, full_name, email, phone, country):
    return supabase.table("users").insert({
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "country": country,
    }).execute()


def get_user(user_id):
    result = (
        supabase.table("users")
        .select(USER_COLUMNS)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return _user_tuple(_one(result.data))


def update_wallet_address(user_id, wallet_address):
    return (
        supabase.table("users")
        .update({"wallet_address": wallet_address})
        .eq("user_id", user_id)
        .execute()
    )


def update_wallet_balance(user_id, amount):
    user = get_user(user_id)
    if not user:
        return False

    new_balance = float(user[7] or 0) + float(amount)

    supabase.table("users").update({
        "wallet_balance": new_balance
    }).eq("user_id", user_id).execute()

    return True


def update_affiliate_balance(user_id, amount):
    user = get_user(user_id)
    if not user:
        return False

    new_balance = float(user[8] or 0) + float(amount)

    supabase.table("users").update({
        "affiliate_balance": new_balance
    }).eq("user_id", user_id).execute()

    return True


def get_wallet_balance(user_id):
    result = (
        supabase.table("users")
        .select("wallet_balance")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return float(row["wallet_balance"] or 0) if row else 0.0


# =====================================
# REFERRAL FUNCTIONS
# =====================================

def set_referrer(user_id, referrer_id):
    return (
        supabase.table("users")
        .update({"referrer_id": referrer_id})
        .eq("user_id", user_id)
        .execute()
    )


def get_referrer(user_id):
    result = (
        supabase.table("users")
        .select("referrer_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return row["referrer_id"] if row else None


def has_first_deposit(user_id):
    result = (
        supabase.table("users")
        .select("first_deposit")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return bool(row and row.get("first_deposit") == 1)


def mark_first_deposit(user_id):
    return (
        supabase.table("users")
        .update({"first_deposit": 1})
        .eq("user_id", user_id)
        .execute()
    )


def add_referral_bonus(user_id, amount):
    return update_affiliate_balance(user_id, amount)


def increment_referrals(user_id):
    result = (
        supabase.table("users")
        .select("referrals")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    if not row:
        return False

    new_count = int(row.get("referrals") or 0) + 1
    supabase.table("users").update({
        "referrals": new_count
    }).eq("user_id", user_id).execute()

    return True


def pay_mining_referral_bonus(user_id, mining_reward):
    referrer_id = get_referrer(user_id)

    if not referrer_id:
        return None

    from config import AFFILIATE_MINING_RATE

    commission = round(
        float(mining_reward) * AFFILIATE_MINING_RATE,
        2,
    )

    add_referral_bonus(referrer_id, commission)

    record_wallet_transaction(
        user_id=referrer_id,
        transaction_type="Affiliate Commission",
        amount=commission,
        reason="5% Mining Referral Commission",
    )

    return referrer_id, commission


# =====================================
# DEPOSIT FUNCTIONS
# =====================================

def add_deposit(
    user_id,
    network,
    amount,
    crypto_amount,
    txid,
    status="Pending",
):
    return supabase.table("deposits").insert({
        "user_id": user_id,
        "network": network,
        "amount": amount,
        "crypto_amount": crypto_amount,
        "txid": txid,
        "status": status,
    }).execute()


def get_user_deposits(user_id):
    result = (
        supabase.table("deposits")
        .select("network,amount,crypto_amount,txid,status")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .execute()
    )
    return [
        tuple(row.get(k) for k in (
            "network", "amount", "crypto_amount", "txid", "status"
        ))
        for row in _rows(result.data)
    ]


def get_pending_deposits():
    result = (
        supabase.table("deposits")
        .select("id,user_id,network,amount,crypto_amount,txid")
        .eq("status", "Pending")
        .order("id", desc=False)
        .execute()
    )
    return [
        tuple(row.get(k) for k in (
            "id", "user_id", "network", "amount", "crypto_amount", "txid"
        ))
        for row in _rows(result.data)
    ]


def get_deposit(deposit_id):
    result = (
        supabase.table("deposits")
        .select("user_id,amount")
        .eq("id", deposit_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return (row["user_id"], row["amount"]) if row else None


def update_deposit_status(deposit_id, status):
    return (
        supabase.table("deposits")
        .update({"status": status})
        .eq("id", deposit_id)
        .execute()
    )


def add_wallet_balance(user_id, amount):
    return update_wallet_balance(user_id, amount)


def deduct_wallet_balance(user_id, amount):
    balance = get_wallet_balance(user_id)

    if balance < float(amount):
        return False

    result = (
        supabase.table("users")
        .update({"wallet_balance": balance - float(amount)})
        .eq("user_id", user_id)
        .execute()
    )

    return bool(result.data)


def admin_wallet_adjustment(user_id, amount, transaction_type, reason):
    user = get_user(user_id)
    if not user:
        return False

    balance = float(user[7] or 0)
    amount = float(amount)

    if transaction_type == "Credit":
        new_balance = balance + amount
    else:
        if balance < amount:
            return False
        new_balance = balance - amount

    result = (
        supabase.table("users")
        .update({"wallet_balance": new_balance})
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        return False

    record_wallet_transaction(
        user_id=user_id,
        transaction_type=transaction_type,
        amount=amount,
        reason=reason,
    )

    return True


def get_wallet_transactions(user_id):
    result = (
        supabase.table("wallet_transactions")
        .select("transaction_type,amount,reason,created_at")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .limit(20)
        .execute()
    )
    return [_wallet_transaction_tuple(row) for row in _rows(result.data)]


def record_wallet_transaction(
    user_id,
    transaction_type,
    amount,
    reason,
):
    return supabase.table("wallet_transactions").insert({
        "user_id": user_id,
        "transaction_type": transaction_type,
        "amount": amount,
        "reason": reason,
    }).execute()


def get_latest_deposit_status(user_id):
    result = (
        supabase.table("deposits")
        .select("status")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return row["status"] if row else "No Deposit"


def get_latest_refund_status(user_id):
    result = (
        supabase.table("refunds")
        .select("status")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return row["status"] if row else "No Refund Request"


# ==========================================
# WITHDRAWALS
# ==========================================

def create_withdrawal(
    user_id,
    cryptocurrency,
    wallet_address,
    amount,
):
    return supabase.table("withdrawals").insert({
        "user_id": user_id,
        "cryptocurrency": cryptocurrency,
        "wallet_address": wallet_address,
        "amount": amount,
    }).execute()


def get_pending_withdrawals():
    result = (
        supabase.table("withdrawals")
        .select("id,user_id,cryptocurrency,wallet_address,amount")
        .eq("status", "Pending")
        .order("id", desc=False)
        .execute()
    )
    return [
        tuple(row.get(k) for k in (
            "id", "user_id", "cryptocurrency", "wallet_address", "amount"
        ))
        for row in _rows(result.data)
    ]


def update_withdrawal_status(
    withdrawal_id,
    status,
    reason=None,
    txid=None,
    completed_at=None,
):
    return (
        supabase.table("withdrawals")
        .update({
            "status": status,
            "rejection_reason": reason,
            "txid": txid,
            "completed_at": completed_at,
        })
        .eq("id", withdrawal_id)
        .execute()
    )


def get_withdrawal(withdrawal_id):
    result = (
        supabase.table("withdrawals")
        .select("user_id,amount,cryptocurrency,wallet_address")
        .eq("id", withdrawal_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return (
        row["user_id"],
        row["amount"],
        row["cryptocurrency"],
        row["wallet_address"],
    ) if row else None


def get_user_withdrawals(user_id):
    result = (
        supabase.table("withdrawals")
        .select(
            "amount,cryptocurrency,wallet_address,status,"
            "rejection_reason,txid,created_at"
        )
        .eq("user_id", user_id)
        .order("id", desc=True)
        .execute()
    )
    return [
        tuple(row.get(k) for k in (
            "amount", "cryptocurrency", "wallet_address",
            "status", "rejection_reason", "txid", "created_at"
        ))
        for row in _rows(result.data)
    ]


# =====================================
# REFUND FUNCTIONS
# =====================================

def add_refund(
    user_id,
    full_name,
    investment_date,
    profile_id,
    investment_amount,
    cryptocurrency,
    exchange_wallet,
    sender_wallet,
    evidence_text,
    evidence_file_ids,
):
    return supabase.table("refunds").insert({
        "user_id": user_id,
        "full_name": full_name,
        "investment_date": investment_date,
        "profile_id": profile_id,
        "investment_amount": investment_amount,
        "cryptocurrency": cryptocurrency,
        "exchange_wallet": exchange_wallet,
        "sender_wallet": sender_wallet,
        "evidence_text": evidence_text,
        "evidence_file_ids": evidence_file_ids,
    }).execute()


def get_pending_refunds():
    result = (
        supabase.table("refunds")
        .select("*")
        .eq("status", "Pending")
        .execute()
    )
    return [_refund_tuple(row) for row in _rows(result.data)]


def update_refund_status(refund_id, status):
    return (
        supabase.table("refunds")
        .update({"status": status})
        .eq("id", refund_id)
        .execute()
    )


def get_refund(refund_id):
    result = (
        supabase.table("refunds")
        .select("user_id,investment_amount")
        .eq("id", refund_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return (
        row["user_id"], row["investment_amount"]
    ) if row else None


def get_user_refunds(user_id):
    result = (
        supabase.table("refunds")
        .select("*")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .execute()
    )
    return [_refund_tuple(row) for row in _rows(result.data)]


# =====================================
# SUPPORT MESSAGE MAPPING
# =====================================

def save_support_message(message_id, user_id):
    return supabase.table("support_messages").upsert({
        "message_id": message_id,
        "user_id": user_id,
    }).execute()


def get_support_user(message_id):
    result = (
        supabase.table("support_messages")
        .select("user_id")
        .eq("message_id", message_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return row["user_id"] if row else None


# =====================================
# KYC FUNCTIONS
# =====================================

def submit_kyc(
    user_id,
    full_name,
    id_document,
    selfie_document,
):
    supabase.table("kyc").upsert({
        "user_id": user_id,
        "full_name": full_name,
        "id_document": id_document,
        "selfie_document": selfie_document,
        "status": "Pending",
    }, on_conflict="user_id").execute()

    return (
        supabase.table("users")
        .update({"kyc_status": "Pending"})
        .eq("user_id", user_id)
        .execute()
    )


def get_kyc(user_id):
    result = (
        supabase.table("kyc")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return _kyc_tuple(_one(result.data))


def get_kyc_status(user_id):
    result = (
        supabase.table("users")
        .select("kyc_status")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _one(result.data)
    return row["kyc_status"] if row else "Not Submitted"


def get_pending_kyc():
    result = (
        supabase.table("kyc")
        .select("user_id,full_name,id_document,selfie_document")
        .eq("status", "Pending")
        .order("id", desc=False)
        .execute()
    )
    return [
        tuple(row.get(k) for k in (
            "user_id", "full_name", "id_document", "selfie_document"
        ))
        for row in _rows(result.data)
    ]


def update_kyc_status(user_id, status):
    supabase.table("kyc").update({
        "status": status
    }).eq("user_id", user_id).execute()

    return (
        supabase.table("users")
        .update({"kyc_status": status})
        .eq("user_id", user_id)
        .execute()
    )


# =====================================
# CLOUD MINING FUNCTIONS
# =====================================

def create_mining_contract(
    user_id,
    hash_power,
    purchase_price,
    daily_income,
    purchase_date,
):
    return supabase.table("mining_contracts").insert({
        "user_id": user_id,
        "hash_power": hash_power,
        "purchase_price": purchase_price,
        "daily_income": daily_income,
        "purchase_date": purchase_date,
        "last_claim": purchase_date,
    }).execute()


def get_active_contracts(user_id):
    result = (
        supabase.table("mining_contracts")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "Active")
        .order("purchase_date", desc=True)
        .execute()
    )
    return [
        _mining_contract_tuple(row)
        for row in _rows(result.data)
    ]


def has_active_contract(user_id):
    result = (
        supabase.table("mining_contracts")
        .select("id")
        .eq("user_id", user_id)
        .eq("status", "Active")
        .limit(1)
        .execute()
    )
    return bool(result.data)


def get_total_hash_power(user_id):
    result = (
        supabase.table("mining_contracts")
        .select("hash_power")
        .eq("user_id", user_id)
        .eq("status", "Active")
        .execute()
    )
    total = sum(float(row.get("hash_power") or 0) for row in _rows(result.data))
    return round(total, 2)


def get_daily_earnings(user_id):
    result = (
        supabase.table("mining_contracts")
        .select("daily_income")
        .eq("user_id", user_id)
        .eq("status", "Active")
        .execute()
    )
    total = sum(float(row.get("daily_income") or 0) for row in _rows(result.data))
    return round(total, 2)


def get_weekly_earnings(user_id):
    return round(get_daily_earnings(user_id) * 7, 2)


def get_monthly_earnings(user_id):
    return round(get_daily_earnings(user_id) * 30, 2)


def get_mining_balance(user_id):
    result = (
        supabase.table("mining_contracts")
        .select("daily_income,last_claim")
        .eq("user_id", user_id)
        .eq("status", "Active")
        .execute()
    )

    total = 0.0
    now = datetime.now()

    for row in _rows(result.data):
        daily_income = float(row.get("daily_income") or 0)
        last = _parse_datetime(row.get("last_claim"))
        elapsed_seconds = (now - last).total_seconds()
        total += (daily_income / 86400) * elapsed_seconds

    return round(total, 2)


def update_last_claim(contract_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return (
        supabase.table("mining_contracts")
        .update({"last_claim": now})
        .eq("id", contract_id)
        .execute()
    )


def save_claim(user_id, contract_id, amount):
    return supabase.table("mining_claims").insert({
        "user_id": user_id,
        "contract_id": contract_id,
        "amount": amount,
        "claim_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }).execute()


def calculate_claim(user_id):
    result = (
        supabase.table("mining_contracts")
        .select("id,daily_income,last_claim")
        .eq("user_id", user_id)
        .eq("status", "Active")
        .execute()
    )

    total = 0.0
    claim_details = []
    now = datetime.now()

    for row in _rows(result.data):
        contract_id = row["id"]
        daily_income = float(row.get("daily_income") or 0)
        last = _parse_datetime(row.get("last_claim"))

        seconds = (now - last).total_seconds()
        earned = (daily_income / 86400) * seconds

        if earned > 0:
            total += earned
            claim_details.append((contract_id, earned))

    return round(total, 2), claim_details
