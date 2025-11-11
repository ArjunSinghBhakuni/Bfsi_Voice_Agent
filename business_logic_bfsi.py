# Core business logic for BFSI voice agent (prototype, no DB).

from typing import Dict, Any
from datetime import date
from sample_data import find_customer
from openai import OpenAI
import os

class BFSIBusinessLogic:
    def __init__(self):
        # Read key from env; if missing, stay in "no-AI" mode
        key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=key) if key else None

    def _naturalize(self, msg: str) -> str:
        """Use GPT to make TTS-friendly, concise, friendly phrasing."""
        if not self.client:
            # No key? Just return the original message (no crash)
            return msg
        try:
            resp = self.client.responses.create(
                model="gpt-4.1-mini",
                input=(
                    "Rephrase for phone voice: concise, warm, plain-English (en-IN), "
                    "no extra fluff.\n\nText:\n" + msg
                ),
                temperature=0.6,
            )
            # Newer SDKs expose .output_text; guard for safety:
            text = getattr(resp, "output_text", None)
            return (text or "").strip() or msg
        except Exception as e:
            print(f"AI rephrase error: {e}")
            return msg


    # --- Intent classification (banking + insurance) ---
    def classify_intent(self, text: str) -> str:
        t = (text or "").lower()
        if any(k in t for k in ["balance", "account", "statement", "transactions"]):
            return "balance_inquiry"
        if any(k in t for k in ["lost card", "stolen card", "block my card", "block card", "hotlist"]):
            return "card_block"
        if any(k in t for k in ["emi", "loan", "due", "installment"]):
            return "emi_info"
        if any(k in t for k in ["claim", "insurance", "policy", "coverage"]):
            return "claim_status"
        if any(k in t for k in ["update phone", "change number", "update mobile", "update address", "update email"]):
            return "update_contact"
        if any(k in t for k in ["help", "agent", "human", "representative"]):
            return "escalation"
        return "fallback"

    # --- Handlers ---
    def handle_balance_inquiry(self, phone: str) -> Dict[str, Any]:
        c = find_customer(phone)
        if not c or not c.get("accounts"):
            return {"success": False, "message": "I couldn't find an eligible account for this number."}
        a = c["accounts"][0]
        last = a.get("last_txn")
        last_line = ""
        if last:
            last_line = f" Your last transaction was a {last['type']} of ₹{last['amount']:.0f} on {last['on'].strftime('%B %d')} at {last['merchant']}."
        msg = (f"Your savings account ending in {a['last4']} has a current balance of ₹{a['balance']:.0f}."
               + last_line + " Would you like a mini statement via SMS?")
        return {"success": True, "message": msg, "data": a}

    def handle_card_block(self, phone: str) -> Dict[str, Any]:
        c = find_customer(phone)
        if not c or not c.get("cards"):
            return {"success": False, "message": "I couldn't find a card linked to this number."}
        card = c["cards"][0]
        if card["blocked"]:
            return {"success": True, "message": f"Your card ending {card['last4']} is already blocked.", "data": card}
        card["blocked"] = True
        card["status"] = "blocked"
        return {"success": True, "message": f"I've blocked your card ending in {card['last4']} immediately. "
                                            f"No further transactions can be made. Do you want a replacement card?"}

    def handle_emi_info(self, phone: str) -> Dict[str, Any]:
        c = find_customer(phone)
        if not c or not c.get("loans"):
            return {"success": False, "message": "I couldn't find a loan linked to this number."}
        l = c["loans"][0]
        msg = (f"Your next EMI of ₹{l['emi']:.0f} is due on {l['due_date'].strftime('%B %d, %Y')}. "
               f"Outstanding principal is ₹{l['outstanding_principal']:.0f}. "
               f"You have {l['tenure_months_left']} months remaining. "
               f"Would you like to explore prepayment options?")
        return {"success": True, "message": msg, "data": l}

    def handle_claim_status(self, phone: str) -> Dict[str, Any]:
        c = find_customer(phone)
        if not c or not c.get("policies"):
            return {"success": False, "message": "I couldn't find an insurance policy linked to this number."}
        p = c["policies"][0]
        cl = p.get("claim")
        if not cl:
            return {"success": True, "message": f"Your {p['type']} policy {p['policy_no']} has no active claims."}
        msg = (f"Your claim {cl['id']} submitted on {cl['submitted_on'].strftime('%B %d, %Y')} "
               f"for ₹{cl['amount']:.0f} is currently {cl['status'].replace('_',' ')}. "
               f"Expected settlement date: {cl['expected_settlement_on'].strftime('%B %d, %Y')}. "
               f"I'll notify you when it's processed.")
        return {"success": True, "message": msg, "data": cl}

    def handle_update_contact(self, phone: str, new_value: str) -> Dict[str, Any]:
        c = find_customer(phone)
        if not c:
            return {"success": False, "message": "I couldn't identify your profile to update details."}
        # Very simple heuristic: detect email vs phone
        if "@" in new_value:
            c["contact"]["email"] = new_value
            what = "email address"
        else:
            c["contact"]["phone"] = new_value if new_value.startswith("+") else "+91" + new_value[-10:]
            what = "mobile number"
        return {"success": True, "message": f"Done. I've updated your {what}. A confirmation has been sent."}

    def generate_response(self, phone: str, user_text: str) -> str:
        intent = self.classify_intent(user_text)
        if intent == "balance_inquiry":
            msg = self.handle_balance_inquiry(phone)["message"]
            return self._naturalize(msg)
        if intent == "card_block":
            msg = self.handle_card_block(phone)["message"]
            return self._naturalize(msg)
        if intent == "emi_info":
            msg = self.handle_emi_info(phone)["message"]
            return self._naturalize(msg)
        if intent == "claim_status":
            msg = self.handle_claim_status(phone)["message"]
            return self._naturalize(msg)
        if intent == "update_contact":
            # naive extraction of last token as new value
            new_value = user_text.split()[-1]
            msg = self.handle_update_contact(phone, new_value)["message"]
            return self._naturalize(msg)
        if intent == "escalation":
            return self._naturalize("Okay, I'll connect you to a human specialist and share the context.")
        return self._naturalize("You can ask about your balance, block a card, EMI details, claim status, or update contact info.")