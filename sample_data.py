from datetime import date

CUSTOMERS = {
    "+919876543210": {
        "name": "Aarav Sharma",
        "segment": "Retail",
        "language": "en-IN",
        "accounts": [
            {"type": "savings", "last4": "4567", "balance": 125430.00, "currency": "INR",
             "last_txn": {"type": "debit", "amount": 2500.00, "merchant": "ABC Store", "on": date(2025, 10, 25)}}
        ],
        "cards": [{"last4": "8912", "status": "active", "network": "VISA", "limit": 200000}],
        "loans": [{"type": "home", "emi": 32450.00, "due_date": date(2025, 11, 5)}],
        "policies": [{"type": "health", "policy_no": "HLP-5566-9988", "status": "active"}],
        "contact": {"email": "aarav@example.com", "phone": "+919876543210"}
    }
}

def find_customer(phone: str):
    return CUSTOMERS.get(phone)
