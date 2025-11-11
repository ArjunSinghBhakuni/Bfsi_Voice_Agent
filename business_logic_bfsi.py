# business_logic_bfsi.py
import os
from openai import OpenAI
from sample_data import find_customer

class BFSIBusinessLogic:
    def __init__(self):
        key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=key) if key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def classify_intent(self, text: str) -> str:
        t = (text or "").lower()
        t = t.replace("cards", "card").replace("blocked", "block").replace("blocking", "block")
        if any(k in t for k in ["balance", "account", "statement", "money", "funds"]):
            return "balance_inquiry"
        if any(k in t for k in ["lost card", "stolen card", "block my card", "block card", "block the card", "hotlist", "deactivate card"]):
            return "card_block"
        if any(k in t for k in ["emi", "loan", "due", "installment", "repayment"]):
            return "emi_info"
        if any(k in t for k in ["claim", "insurance", "policy", "coverage"]):
            return "claim_status"
        if any(k in t for k in ["update phone", "change number", "update mobile", "update email", "change email", "update address"]):
            return "update_contact"
        if any(k in t for k in ["agent", "human", "representative", "talk to person"]):
            return "escalation"
        return "fallback"

    def handle_card_block(self, phone: str):
        c = find_customer(phone)
        if not c or not c.get("cards"):
            return {"success": False, "message": "I couldn't find a card linked to this number."}
        card = c["cards"][0]
        if card.get("blocked"):
            return {"success": True, "message": f"Your card ending {card['last4']} is already blocked."}
        card["blocked"] = True
        card["status"] = "blocked"
        return {"success": True, "message": f"I've blocked your card ending in {card['last4']} immediately. Would you like a replacement card?"}

    def handle_balance_inquiry(self, phone):
        c = find_customer(phone)
        if not c or not c.get("accounts"):
            return {"success": False, "message": "No account found."}
        a = c["accounts"][0]
        return {"success": True, "message": f"Your savings account ending in {a['last4']} has a balance of ₹{a['balance']:.0f}. Would you like a mini statement sent via SMS?"}

    def handle_emi_info(self, phone):
        c = find_customer(phone)
        if not c or not c.get("loans"):
            return {"success": False, "message": "No loans found."}
        l = c["loans"][0]
        return {"success": True, "message": f"Your next EMI of ₹{l['emi']:.0f} is due on {l['due_date'].strftime('%b %d, %Y')}."}

    def handle_claim_status(self, phone):
        c = find_customer(phone)
        if not c or not c.get("policies"):
            return {"success": False, "message": "No policies found."}
        p = c["policies"][0]
        claim = p.get("claim")
        if not claim:
            return {"success": True, "message": f"Your {p['type']} policy {p['policy_no']} has no active claims."}
        return {"success": True, "message": f"Your claim {claim['id']} submitted on {claim['submitted_on']} for ₹{claim['amount']:.0f} is currently {claim['status']}."}

    def generate_response(self, phone, query):
        intent = self.classify_intent(query)
        if intent == "balance_inquiry":
            msg = self.handle_balance_inquiry(phone)["message"]
        elif intent == "card_block":
            msg = self.handle_card_block(phone)["message"]
        elif intent == "emi_info":
            msg = self.handle_emi_info(phone)["message"]
        elif intent == "claim_status":
            msg = self.handle_claim_status(phone)["message"]
        else:
            msg = "You can check your balance, block a card, get EMI details, check claim status, or update contact info."
        if self.client:
            try:
                resp = self.client.responses.create(model=self.model, input=f"Rephrase for friendly voice tone: {msg}", temperature=0.7)
                return resp.output_text or msg
            except Exception:
                return msg
        return msg
