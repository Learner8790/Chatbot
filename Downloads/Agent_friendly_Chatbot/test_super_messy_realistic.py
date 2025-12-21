"""
SUPER MESSY REALISTIC TEST

Real Indian user behavior:
- Heavy sarcasm and frustration
- Twitter/WhatsApp style complaints
- Code-switching mid-sentence
- Emojis and punctuation abuse
- Regional slang (yaar, bhai, arrey)
- Voice message transcription errors
- Incomplete thoughts
- Multiple issues in one message

This is what ACTUAL customer care receives.
"""

import anthropic
import json
from sentence_transformers import SentenceTransformer
import numpy as np

API_KEY = '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'
client = anthropic.Anthropic(api_key=API_KEY)


class CostTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0

    def add(self, inp, out):
        self.input_tokens += inp
        self.output_tokens += out
        self.calls += 1

    def get_cost(self, model="haiku"):
        if model == "sonnet":
            return (self.input_tokens / 1_000_000) * 3 + (self.output_tokens / 1_000_000) * 15
        return (self.input_tokens / 1_000_000) * 0.25 + (self.output_tokens / 1_000_000) * 1.25


# Intents
INTENTS = {
    "card_not_working": "Card Not Working",
    "activate_card": "Activate Card",
    "lost_stolen_card": "Lost Or Stolen Card",
    "block_card": "Block Card",
    "card_delivery": "Card Delivery Status",
    "change_pin": "Change Pin",
    "forgot_pin": "Forgot Pin",
    "pin_blocked": "Pin Blocked",
    "check_balance": "Check Balance",
    "transfer_money": "Transfer Money",
    "failed_transfer": "Failed Transfer",
    "pending_transfer": "Pending Transfer",
    "wrong_transaction": "Wrong Or Fraud Transaction",
    "refund_status": "Refund Status",
    "increase_limit": "Increase Limit",
    "account_locked": "Account Locked",
    "reset_password": "Reset Password",
    "update_mobile": "Update Mobile Number",
    "update_kyc": "Update KYC",
    "link_aadhar": "Link Aadhar",
    "upi_issue": "UPI Issue",
    "app_not_working": "App Not Working",
    "netbanking_issue": "Netbanking Issue",
    "customer_care": "Contact Customer Care",
    "file_complaint": "File Complaint",
    "loan_inquiry": "Loan Inquiry",
    "emi_issue": "EMI Issue",
    "atm_issue": "ATM Issue",
    "cheque_issue": "Cheque Issue",
    "account_statement": "Account Statement",
}

# Agent-friendly metadata with Hinglish
AGENT_FRIENDLY_METADATA = {
    "card_not_working": "Card not working, declined, error | kaam nhi kr rha, chal nhi rha, decline ho gya",
    "activate_card": "Activate new card, start using card | card activate karna, chalu karna, new card",
    "lost_stolen_card": "Card lost or stolen, report missing | card kho gya, chori, missing, gayab",
    "block_card": "Block or freeze card | card block karo, band karo, freeze",
    "card_delivery": "Card delivery status, when arriving | card kab ayega, delivery, shipping status",
    "change_pin": "Change existing PIN | pin change karna, naya pin, update pin",
    "forgot_pin": "Forgot PIN, recover PIN | pin bhul gya, yaad nhi, pin kya tha",
    "pin_blocked": "PIN blocked after wrong attempts | pin block, lock ho gya, wrong pin",
    "check_balance": "Check account balance | balance kitna, paisa kitna, available balance",
    "transfer_money": "Send money, make payment | paise bhejne, transfer karna, payment",
    "failed_transfer": "Transfer failed, money stuck | transfer fail, paisa nhi gya, failed",
    "pending_transfer": "Transfer pending, not complete | pending, processing, abhi tak nhi",
    "wrong_transaction": "Fraud, unknown transaction, didn't do this | fraud, maine nhi kiya, galat transaction",
    "refund_status": "Refund status, money back | refund kab, paisa wapas, refund nhi aaya",
    "increase_limit": "Increase transaction limit | limit badha do, zyada limit, increase",
    "account_locked": "Account locked, can't access | account lock, login nhi ho rha, band",
    "reset_password": "Reset password, forgot password | password bhul gya, reset karo, new password",
    "update_mobile": "Update mobile number | number change, mobile update, new number",
    "update_kyc": "KYC update, verification | kyc karna, documents, verification",
    "link_aadhar": "Link Aadhar card | aadhar link, aadhar connect, aadhar update",
    "upi_issue": "UPI not working, GPay PhonePe issue | upi nhi chal rha, gpay, phonepe, bhim",
    "app_not_working": "Mobile app crash, not opening | app nhi chal rha, crash, open nhi",
    "netbanking_issue": "Netbanking problem, website issue | netbanking, website, online banking nhi",
    "customer_care": "Talk to human, contact support | baat karo, human agent, customer care",
    "file_complaint": "File complaint, bad service | complaint, shikayat, problem report",
    "loan_inquiry": "Loan information, apply loan | loan chahiye, loan apply, personal loan",
    "emi_issue": "EMI problem, missed EMI | emi, installment, emi bounce",
    "atm_issue": "ATM problem, cash not dispensed | atm, cash nhi nikla, atm issue",
    "cheque_issue": "Cheque book, cheque problem | cheque book, cheque clear nhi hua",
    "account_statement": "Account statement, transaction history | statement chahiye, history",
}

# SUPER MESSY REALISTIC QUERIES
# Like actual Indian users on Twitter/WhatsApp complaints
SUPER_MESSY_QUERIES = [
    # Heavy sarcasm
    {"query": "waah kya service hai card 3 din se kaam nhi kr rha aur aap log chill kr rhe", "intent": "card_not_working"},
    {"query": "amazing yaar 10 baar try kiya transfer nhi ho rha wah wah", "intent": "failed_transfer"},
    {"query": "bahut badiya app hai crash hi crash thank you so much", "intent": "app_not_working"},
    {"query": "kya zabardast bank hai refund ke liye 1 mahina wait karo waah", "intent": "refund_status"},
    {"query": "superb customer care 2 ghante hold pe rakha fir call cut gaya claps", "intent": "customer_care"},

    # Extreme frustration (caps, multiple punctuation)
    {"query": "HELLO ANYBODY THERE??? MY MONEY IS STUCK SINCE 5 DAYS!!!!!", "intent": "pending_transfer"},
    {"query": "KYA HAI YE BAKWAS CARD KAAM NHI KR RHA KITNI BAAR BOLU???", "intent": "card_not_working"},
    {"query": "ARE YOU GUYS EVEN WORKING??? ACCOUNT LOCK SINCE MORNING", "intent": "account_locked"},
    {"query": "WORST BANK EVERRRRR MY 50000 RS GONE WHERE IS IT??????", "intent": "failed_transfer"},
    {"query": "URGENT URGENT URGENT card chori ho gya koi suno toh", "intent": "lost_stolen_card"},

    # Code-switching mid-sentence
    {"query": "bhai mera card activate kaise karu its been 2 weeks since i received it", "intent": "activate_card"},
    {"query": "yaar balance check karna hai but app open hi nhi ho rha what to do", "intent": "app_not_working"},
    {"query": "arrey last week ka transfer abhi tak pending hai when will it complete", "intent": "pending_transfer"},
    {"query": "boss pin block ho gya because of wrong attempts ab kya karu tell me", "intent": "pin_blocked"},
    {"query": "bro mere account me 10000 ka unknown transaction hai i didnt do this", "intent": "wrong_transaction"},

    # WhatsApp style (short, incomplete)
    {"query": "hello card issue", "intent": "card_not_working"},
    {"query": "hi balance?", "intent": "check_balance"},
    {"query": "haan wo transfer wala", "intent": "pending_transfer"},
    {"query": "pin problm", "intent": "forgot_pin"},
    {"query": "stmt send kro", "intent": "account_statement"},
    {"query": "koi hai??", "intent": "customer_care"},
    {"query": "urgent help", "intent": "customer_care"},
    {"query": "refnd", "intent": "refund_status"},

    # Voice message transcription style (run-on, no punctuation)
    {"query": "haan bhai wo mera card hai na usme kuch problem aa gyi hai matlab kaam nhi kr rha hai aaj subah se try kr rha hu shop pe bhi decline ho gya", "intent": "card_not_working"},
    {"query": "are sun mujhe apna number change krna hai purana number band ho gya hai toh naya dalna hai kaise karu", "intent": "update_mobile"},
    {"query": "dekh yaar mera paisa transfer kiya tha 3 din pehle abhi tak nhi gya samne wale ko bol rha pending hai kya scene hai", "intent": "pending_transfer"},
    {"query": "bhai sunn ek transaction dikha rha hai jo maine kiya hi nhi 5000 ka fraud lag rha hai mujhe", "intent": "wrong_transaction"},

    # Regional slang variations
    {"query": "abe oye card block krdo jaldi", "intent": "block_card"},
    {"query": "bey mere card ka kya hua aaya ki nhi", "intent": "card_delivery"},
    {"query": "arey bapu loan ke baare me btao", "intent": "loan_inquiry"},
    {"query": "oye hoye pin galat dal diya block hogya", "intent": "pin_blocked"},
    {"query": "paaji atm se cash nhi nikla", "intent": "atm_issue"},

    # Typos + Hinglish combo
    {"query": "actiavte kro plzz crad", "intent": "activate_card"},
    {"query": "passowrd yaad nhi chnage krna h", "intent": "reset_password"},
    {"query": "transferr stuck h 2 dinn se", "intent": "pending_transfer"},
    {"query": "upii kaam nhi krr rhaa phonpay", "intent": "upi_issue"},
    {"query": "emii bounec hogayi halp", "intent": "emi_issue"},

    # Emoji abuse (text with implied emoji context)
    {"query": "card kho gya crying face please help", "intent": "lost_stolen_card"},
    {"query": "finally refund aaya thank god praying hands", "intent": "refund_status"},
    {"query": "angry face worst service ever fire emoji", "intent": "file_complaint"},
    {"query": "atm ne card kha liya shocked face", "intent": "atm_issue"},
    {"query": "app crash thumbs down emoji", "intent": "app_not_working"},

    # Multi-issue messages (should pick primary)
    {"query": "bhai pehle toh card block kro urgent uske baad new card bhejo", "intent": "block_card"},
    {"query": "transfer fail hua refund kab aayega aur complaint bhi krni hai", "intent": "failed_transfer"},
    {"query": "app bhi nhi chal rha netbanking bhi band hai kuch toh kro", "intent": "app_not_working"},
    {"query": "pin change krna hai aur limit bhi badha do", "intent": "change_pin"},

    # Threats/ultimatums (common in complaints)
    {"query": "agar aaj refund nhi aaya toh rbi me complaint krunga", "intent": "refund_status"},
    {"query": "card activate nhi hua toh account band krwa dunga", "intent": "activate_card"},
    {"query": "last warning hai transfer complete kro warna legal action", "intent": "pending_transfer"},
    {"query": "twitter pe viral krunga agar issue solve nhi hua", "intent": "file_complaint"},

    # Questions that aren't really questions
    {"query": "kab tak wait kru card ke liye bolo toh", "intent": "card_delivery"},
    {"query": "kyc documents kaunse chahiye batao toh sahi", "intent": "update_kyc"},
    {"query": "aadhar link hai ya nhi check kro na", "intent": "link_aadhar"},
    {"query": "loan milega ya nhi seedha bolo", "intent": "loan_inquiry"},

    # Very informal/slang heavy
    {"query": "chl be balance bta", "intent": "check_balance"},
    {"query": "hn hn wo cheque wala scene", "intent": "cheque_issue"},
    {"query": "fir se atm ne paisa nhi diya bc", "intent": "atm_issue"},
    {"query": "bhai sahab kya kr rhe ho app thik kro", "intent": "app_not_working"},
    {"query": "sun be jaldi kro transfer urgent h", "intent": "transfer_money"},

    # Passive aggressive
    {"query": "its ok take your time its only been 10 days for my refund no rush", "intent": "refund_status"},
    {"query": "no problem i love waiting 30 mins for customer care very relaxing", "intent": "customer_care"},
    {"query": "sure keep my transfer pending forever i dont need that money anyway", "intent": "pending_transfer"},
    {"query": "lovely that my card doesnt work just when i need it most wonderful", "intent": "card_not_working"},

    # Genuine confused users
    {"query": "mujhe kuch samajh nhi aa rha card mila hai kya karu isse", "intent": "activate_card"},
    {"query": "pata nhi kya hua paisa nhi gya shayad", "intent": "failed_transfer"},
    {"query": "wo kya hota hai upi wala kaise karte hain", "intent": "upi_issue"},
    {"query": "ek number aaya tha otp ka wo kya tha", "intent": "wrong_transaction"},
    {"query": "mujhe apna balance dekhna hai kahan dikhega", "intent": "check_balance"},
]


class BasicVectorRouter:
    def __init__(self, metadata):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.doc_embeddings = {}
        for intent, text in metadata.items():
            self.doc_embeddings[intent] = self.embedder.encode(text)

    def route(self, query):
        q_emb = self.embedder.encode(query)
        best_intent, best_score = None, -1
        for intent, emb in self.doc_embeddings.items():
            score = float(np.dot(emb, q_emb))
            if score > best_score:
                best_score = score
                best_intent = intent
        return best_intent, best_score


class AgentFriendlyVectorRouter:
    def __init__(self, metadata):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.doc_embeddings = {}
        for intent, text in metadata.items():
            self.doc_embeddings[intent] = self.embedder.encode(text)

    def route(self, query):
        q_emb = self.embedder.encode(query)
        best_intent, best_score = None, -1
        for intent, emb in self.doc_embeddings.items():
            score = float(np.dot(emb, q_emb))
            if score > best_score:
                best_score = score
                best_intent = intent
        return best_intent, best_score


class BasicLLMRouter:
    def __init__(self, intents, tracker):
        self.intents = intents
        self.tracker = tracker
        self.intents_list = "\n".join([f"- {k}: {v}" for k, v in intents.items()])

    def route(self, query):
        prompt = f"""You are a banking chatbot. Route this customer query to the correct intent.

The query may be in Hinglish (Hindi+English mix), have typos, slang, sarcasm, or be informal.
Focus on what the user ACTUALLY needs, not their tone.

INTENTS:
{self.intents_list}

CUSTOMER QUERY: "{query}"

Reply with ONLY the intent name (like "card_not_working" or "transfer_money"). Nothing else."""

        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=30,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        self.tracker.add(msg.usage.input_tokens, msg.usage.output_tokens)

        response = msg.content[0].text.strip().lower().replace(" ", "_")
        for intent in self.intents.keys():
            if intent in response:
                return intent, 1.0
        return response, 0.5


def categorize_query(query):
    """Categorize query type"""
    q = query.lower()

    if any(w in q for w in ['waah', 'wah', 'amazing', 'superb', 'thank you so much', 'lovely', 'its ok']):
        return "sarcastic"
    elif q.isupper() or q.count('?') > 2 or q.count('!') > 2:
        return "frustrated"
    elif len(query.split()) <= 3:
        return "vague"
    elif any(w in q for w in ['bhai', 'yaar', 'arrey', 'bro', 'boss', 'paaji', 'abe', 'oye']):
        return "slang"
    elif any(w in q for w in ['emoji', 'face', 'crying', 'praying']):
        return "emoji"
    else:
        return "hinglish"


def run_super_messy_test():
    print("=" * 80)
    print("SUPER MESSY REALISTIC INDIAN USER TEST")
    print("=" * 80)
    print()
    print(f"Total queries: {len(SUPER_MESSY_QUERIES)}")
    print(f"Intents: {len(INTENTS)}")
    print()

    # Categorize
    categories = {}
    for q in SUPER_MESSY_QUERIES:
        cat = categorize_query(q["query"])
        categories[cat] = categories.get(cat, 0) + 1

    print("Query breakdown:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    print()

    # Initialize
    tracker_basic = CostTracker()

    basic_vector = BasicVectorRouter(INTENTS)
    agent_vector = AgentFriendlyVectorRouter(AGENT_FRIENDLY_METADATA)
    basic_llm = BasicLLMRouter(INTENTS, tracker_basic)

    results = {
        "basic_vector": {"total": 0, "correct": 0, "by_cat": {}},
        "agent_vector": {"total": 0, "correct": 0, "by_cat": {}},
        "basic_llm": {"total": 0, "correct": 0, "by_cat": {}},
    }

    errors = {k: [] for k in results.keys()}

    print("Testing all approaches on SUPER MESSY data...")
    print("-" * 80)

    for i, test in enumerate(SUPER_MESSY_QUERIES):
        query = test["query"]
        expected = test["intent"]
        cat = categorize_query(query)

        # Initialize category tracking
        for approach in results.keys():
            if cat not in results[approach]["by_cat"]:
                results[approach]["by_cat"][cat] = {"correct": 0, "total": 0}
            results[approach]["by_cat"][cat]["total"] += 1
            results[approach]["total"] += 1

        # Basic Vector
        pred, _ = basic_vector.route(query)
        if pred == expected:
            results["basic_vector"]["correct"] += 1
            results["basic_vector"]["by_cat"][cat]["correct"] += 1
        else:
            errors["basic_vector"].append({"q": query[:50], "exp": expected, "got": pred, "cat": cat})

        # Agent-Friendly Vector
        pred, _ = agent_vector.route(query)
        if pred == expected:
            results["agent_vector"]["correct"] += 1
            results["agent_vector"]["by_cat"][cat]["correct"] += 1
        else:
            errors["agent_vector"].append({"q": query[:50], "exp": expected, "got": pred, "cat": cat})

        # Basic LLM
        pred, _ = basic_llm.route(query)
        if pred == expected:
            results["basic_llm"]["correct"] += 1
            results["basic_llm"]["by_cat"][cat]["correct"] += 1
        else:
            errors["basic_llm"].append({"q": query[:50], "exp": expected, "got": pred, "cat": cat})

        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(SUPER_MESSY_QUERIES)}...")

    # Calculate accuracies
    total = len(SUPER_MESSY_QUERIES)

    print()
    print("=" * 80)
    print("OVERALL RESULTS")
    print("=" * 80)
    print()

    bv_acc = results["basic_vector"]["correct"] / total * 100
    av_acc = results["agent_vector"]["correct"] / total * 100
    bl_acc = results["basic_llm"]["correct"] / total * 100

    print(f"{'Approach':<35} {'Accuracy':<25} {'Cost'}")
    print("-" * 75)
    print(f"{'Basic Vector':<35} {results['basic_vector']['correct']}/{total} ({bv_acc:.1f}%){'':<10} $0.00")
    print(f"{'Agent-Friendly Vector':<35} {results['agent_vector']['correct']}/{total} ({av_acc:.1f}%){'':<10} $0.00")
    print(f"{'Basic LLM (Haiku)':<35} {results['basic_llm']['correct']}/{total} ({bl_acc:.1f}%){'':<10} ${tracker_basic.get_cost():.4f}")

    print()
    print("=" * 80)
    print("ACCURACY BY QUERY TYPE")
    print("=" * 80)
    print()

    print(f"{'Category':<15} {'Basic Vec':<18} {'Agent Vec':<18} {'Basic LLM':<18}")
    print("-" * 70)

    for cat in sorted(categories.keys()):
        bv_cat = results["basic_vector"]["by_cat"].get(cat, {"correct": 0, "total": 1})
        av_cat = results["agent_vector"]["by_cat"].get(cat, {"correct": 0, "total": 1})
        bl_cat = results["basic_llm"]["by_cat"].get(cat, {"correct": 0, "total": 1})

        bv_pct = bv_cat["correct"] / bv_cat["total"] * 100
        av_pct = av_cat["correct"] / av_cat["total"] * 100
        bl_pct = bl_cat["correct"] / bl_cat["total"] * 100

        print(f"{cat:<15} {bv_cat['correct']}/{bv_cat['total']} ({bv_pct:.0f}%){'':<6} {av_cat['correct']}/{av_cat['total']} ({av_pct:.0f}%){'':<6} {bl_cat['correct']}/{bl_cat['total']} ({bl_pct:.0f}%)")

    # Error samples
    print()
    print("=" * 80)
    print("SAMPLE ERRORS (showing hardest cases)")
    print("=" * 80)
    print()

    print("BASIC VECTOR FAILURES:")
    for e in errors["basic_vector"][:8]:
        print(f"  [{e['cat']}] \"{e['q']}...\"")
        print(f"       Expected: {e['exp']}, Got: {e['got']}")
    print()

    print("AGENT-FRIENDLY VECTOR FAILURES:")
    for e in errors["agent_vector"][:8]:
        print(f"  [{e['cat']}] \"{e['q']}...\"")
        print(f"       Expected: {e['exp']}, Got: {e['got']}")
    print()

    print("BASIC LLM FAILURES:")
    for e in errors["basic_llm"][:8]:
        print(f"  [{e['cat']}] \"{e['q']}...\"")
        print(f"       Expected: {e['exp']}, Got: {e['got']}")

    # Honest assessment
    print()
    print("=" * 80)
    print("HONEST ASSESSMENT: SUPER MESSY INDIAN DATA")
    print("=" * 80)
    print()

    print(f"Basic Vector:         {bv_acc:.1f}%")
    print(f"Agent-Friendly Vector: {av_acc:.1f}% ({av_acc - bv_acc:+.1f}% vs basic)")
    print(f"Basic LLM:            {bl_acc:.1f}%")
    print()

    best = max(bv_acc, av_acc, bl_acc)
    if best >= 85:
        print(f"VERDICT: {best:.1f}% on SUPER MESSY data is EXCELLENT")
        print("Ready for production with human fallback for edge cases.")
    elif best >= 70:
        print(f"VERDICT: {best:.1f}% on SUPER MESSY data is GOOD")
        print("Acceptable for production, but will need human escalation.")
    else:
        print(f"VERDICT: {best:.1f}% on SUPER MESSY data needs work")
        print("Too many misroutes for production use.")

    print()
    print("KEY INSIGHTS:")
    print(f"  - Sarcasm handling: {'Good' if bl_acc > 80 else 'Needs work'}")
    print(f"  - Hinglish handling: {'Good' if bl_acc > 80 else 'Needs work'}")
    print(f"  - Agent-friendly improvement: {av_acc - bv_acc:+.1f}% for vector")
    print(f"  - LLM advantage over vector: {bl_acc - max(bv_acc, av_acc):+.1f}%")

    return {
        "basic_vector": bv_acc,
        "agent_vector": av_acc,
        "basic_llm": bl_acc,
        "agent_improvement": av_acc - bv_acc,
        "llm_cost": tracker_basic.get_cost(),
        "by_category": {
            "basic_vector": {k: v["correct"]/v["total"]*100 for k,v in results["basic_vector"]["by_cat"].items()},
            "agent_vector": {k: v["correct"]/v["total"]*100 for k,v in results["agent_vector"]["by_cat"].items()},
            "basic_llm": {k: v["correct"]/v["total"]*100 for k,v in results["basic_llm"]["by_cat"].items()},
        }
    }


if __name__ == "__main__":
    results = run_super_messy_test()

    with open("super_messy_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to super_messy_results.json")
