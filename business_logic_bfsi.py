# business_logic_bfsi.py
import os
from openai import OpenAI
from sample_data import find_customer

class BFSIBusinessLogic:
    def __init__(self):
        self.key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.key) if self.key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _naturalize(self, msg: str) -> str:
        if not self.client:
            return msg
        try:
            resp = self.client.responses.create(model=self.model, input=f"Rephrase for phone voice (short): {msg}", temperature=0.6)
            # try to read output safely
            out = getattr(resp, "output", None)
            if out and len(out) and hasattr(out[0], "content"):
                # Newer SDK shapes
                text_parts = []
                for block in out:
                    if isinstance(block, dict):
                        # fallback
                        text_parts.append(block.get("text",""))
                    else:
                        # try attribute access
                        for c in getattr(block,"content",[]):
                            text_parts.append(getattr(c,"text", "") or c.get("text",""))
                return " ".join([p for p in text_parts if p]).strip() or msg
            # fallback to output_text
            text = getattr(resp, "output_text", None)
            return (text or "").strip() or msg
        except Exception as e:
            print("AI error:", e)
            return msg

    # keep your existing handlers here (balance, card_block, etc.)
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

    def handle_balance_inquiry(self, phone: str):
        c = find_customer(phone)
        if not c or not c.get("accounts"):
            return {"success": False, "message": "I couldn't find an eligible account for this number."}
        a = c["accounts"][0]
        msg = f"Your savings account ending in {a['last4']} has a current balance of ₹{a['balance']:.0f}. Would you like a mini statement via SMS?"
        return {"success": True, "message": msg, "data": a}

    def handle_card_block(self, phone: str):
        c = find_customer(phone)
        if not c or not c.get("cards"):
            return {"success": False, "message": "I couldn't find a card linked to this number."}
        card = c["cards"][0]
        if card.get("blocked"):
            return {"success": True, "message": f"Your card ending {card['last4']} is already blocked."}
        card["blocked"] = True
        card["status"] = "blocked"
        return {"success": True, "message": f"I've blocked your card ending in {card['last4']} immediately. Do you want a replacement card?"}

    def handle_emi_info(self, phone: str):
        c = find_customer(phone)
        if not c or not c.get("loans"):
            return {"success": False, "message": "I couldn't find a loan linked to this number."}
        l = c["loans"][0]
        msg = f"Your next EMI of ₹{l['emi']:.0f} is due on {l['due_date'].strftime('%B %d, %Y')}. Outstanding principal is ₹{l['outstanding_principal']:.0f}."
        return {"success": True, "message": msg, "data": l}

    def handle_claim_status(self, phone: str):
        c = find_customer(phone)
        if not c or not c.get("policies"):
            return {"success": False, "message": "I couldn't find an insurance policy linked to this number."}
        p = c["policies"][0]
        cl = p.get("claim")
        if not cl:
            return {"success": True, "message": f"Your {p['type']} policy {p['policy_no']} has no active claims."}
        msg = f"Your claim {cl['id']} submitted on {cl['submitted_on'].strftime('%B %d, %Y')} for ₹{cl['amount']:.0f} is {cl['status']}. Expected settlement: {cl['expected_settlement_on'].strftime('%B %d, %Y')}."
        return {"success": True, "message": msg, "data": cl}

    def handle_update_contact(self, phone: str, new_value: str):
        c = find_customer(phone)
        if not c:
            return {"success": False, "message": "I couldn't identify your profile to update details."}
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
            return self._naturalize(self.handle_balance_inquiry(phone)["message"])
        if intent == "card_block":
            return self._naturalize(self.handle_card_block(phone)["message"])
        if intent == "emi_info":
            return self._naturalize(self.handle_emi_info(phone)["message"])
        if intent == "claim_status":
            return self._naturalize(self.handle_claim_status(phone)["message"])
        if intent == "update_contact":
            new_value = user_text.split()[-1]
            return self._naturalize(self.handle_update_contact(phone, new_value)["message"])
        if intent == "escalation":
            return self._naturalize("Okay, I'll connect you to a human specialist and share the context.")
        return self._naturalize("You can ask about your balance, block a card, EMI details, claim status, or update contact info.")
