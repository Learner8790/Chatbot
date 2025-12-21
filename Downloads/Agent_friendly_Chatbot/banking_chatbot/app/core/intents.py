"""
Intent management system for Banking Chatbot.
Handles intent definitions, responses, and agent-friendly metadata.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import json


class IntentCategory(str, Enum):
    """Categories for banking intents."""
    CARD_MANAGEMENT = "card_management"
    ACCOUNT = "account"
    TRANSFERS = "transfers"
    PAYMENTS = "payments"
    SECURITY = "security"
    SUPPORT = "support"
    REWARDS = "rewards"
    LOANS = "loans"


class Intent(BaseModel):
    """Intent definition with all metadata."""
    id: str
    name: str
    category: IntentCategory
    description: str

    # Response templates
    response_template: str
    follow_up_questions: List[str] = Field(default_factory=list)

    # Agent-friendly metadata (helps LLM understand better)
    matches_when: str
    does_not_match_when: str
    key_signals: List[str] = Field(default_factory=list)
    hinglish_variants: List[str] = Field(default_factory=list)

    # Escalation settings
    requires_human: bool = False
    priority: int = Field(default=5, ge=1, le=10)  # 1=lowest, 10=highest

    # Additional context
    example_queries: List[str] = Field(default_factory=list)
    related_intents: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class IntentManager:
    """Manages all banking intents and their metadata."""

    def __init__(self):
        self._intents: Dict[str, Intent] = {}
        self._load_default_intents()

    def _load_default_intents(self):
        """Load default banking intents."""
        default_intents = [
            # Card Management
            Intent(
                id="activate_card",
                name="Activate Card",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Activate a new debit or credit card",
                response_template="To activate your card, please follow these steps:\n1. Log into your mobile banking app\n2. Go to Cards > Manage Cards\n3. Select your new card and tap 'Activate'\n4. Enter the CVV from the back of your card\n\nYour card will be active within 5 minutes.",
                follow_up_questions=["Would you like me to guide you through the app?", "Is this a credit card or debit card?"],
                matches_when="User wants to ACTIVATE or START USING a new card they just received",
                does_not_match_when="Card is not working, blocked, lost, or any other card issue",
                key_signals=["activate", "new card", "start using", "received card", "just got card"],
                hinglish_variants=["card activate karna hai", "naya card chalu karo", "card shuru karna hai"],
                example_queries=[
                    "How do I activate my new card?",
                    "Just received my card, how to start using it?",
                    "bhai mera naya card activate kaise hoga"
                ],
                related_intents=["card_not_working", "card_delivery_status"]
            ),
            Intent(
                id="block_card",
                name="Block Card",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Block a lost or stolen card immediately",
                response_template="I'm blocking your card immediately for security. Your card ending in ****{last4} has been blocked.\n\nNext steps:\n1. If stolen, please file a police report\n2. Order a replacement card (arrives in 3-5 days)\n3. Review recent transactions for unauthorized activity\n\nWould you like to order a replacement now?",
                follow_up_questions=["Is this due to loss or theft?", "Would you like a replacement card?"],
                matches_when="User's card is LOST, STOLEN, or they want to BLOCK it immediately",
                does_not_match_when="Card is simply not working, needs activation, or temporary issue",
                key_signals=["block", "lost", "stolen", "gaya", "kho gaya", "chori", "freeze", "stop"],
                hinglish_variants=["card block karo", "card kho gaya", "card chori ho gaya", "card band karo"],
                priority=10,  # High priority - security
                example_queries=[
                    "Block my card NOW!",
                    "My card was stolen",
                    "abe oye card block krdo jaldi"
                ],
                related_intents=["report_fraud", "order_replacement_card"]
            ),
            Intent(
                id="card_not_working",
                name="Card Not Working",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Troubleshoot card that isn't working",
                response_template="I understand your card isn't working. Let me help troubleshoot:\n\n1. Is the card activated? (New cards need activation)\n2. Is the PIN correct? (3 wrong attempts = temporary block)\n3. Is there sufficient balance?\n4. Is international usage enabled? (If abroad)\n\nWhich of these might be the issue?",
                follow_up_questions=["Is this for ATM or POS?", "Is this happening everywhere or specific merchant?"],
                matches_when="Card is DECLINING, NOT WORKING, being REJECTED at transactions",
                does_not_match_when="Card is lost/stolen, or user wants to block it, or card hasn't arrived",
                key_signals=["not working", "declined", "rejected", "kaam nahi kar raha", "nahi chal raha"],
                hinglish_variants=["card kaam nahi kar raha", "card nahi chal raha", "transaction fail ho raha"],
                example_queries=[
                    "My card got declined at the store",
                    "waah kya service hai card 3 din se kaam nhi kr rha",
                    "why is my card not working???"
                ],
                related_intents=["activate_card", "check_balance", "increase_limit"]
            ),
            Intent(
                id="card_delivery_status",
                name="Card Delivery Status",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Check status of card delivery",
                response_template="Let me check your card delivery status.\n\nYour card was dispatched on {dispatch_date} via {courier}.\nTracking ID: {tracking_id}\nExpected delivery: {expected_date}\n\nYou can also track at: {tracking_url}",
                follow_up_questions=["Is the delivery address correct?", "Would you like SMS updates?"],
                matches_when="User is waiting for card to ARRIVE, asking about DELIVERY or SHIPPING status",
                does_not_match_when="Card has already arrived, or asking about card features",
                key_signals=["where is my card", "card delivery", "when will card come", "track card", "kab aayega"],
                hinglish_variants=["card kab aayega", "mera card kahan hai", "card delivery status"],
                example_queries=[
                    "Where is my card?",
                    "It's been 10 days still no card!",
                    "card kab tak aayega bhai"
                ],
                related_intents=["order_replacement_card", "activate_card"]
            ),
            Intent(
                id="order_physical_card",
                name="Order Physical Card",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Order a new physical card",
                response_template="I'll help you order a new card. Please confirm:\n\n1. Card Type: {card_type}\n2. Delivery Address: {address}\n3. Fee: Rs. {fee} (if applicable)\n\nThe card will be delivered in 5-7 business days. Shall I proceed?",
                follow_up_questions=["Is the address correct?", "Would you prefer express delivery?"],
                matches_when="User wants to ORDER or GET a new physical card",
                does_not_match_when="Asking about existing card, virtual card, or card features",
                key_signals=["order card", "new card chahiye", "get physical card", "apply for card"],
                hinglish_variants=["naya card chahiye", "card mangwana hai", "physical card order karna hai"],
                example_queries=[
                    "I want to order a new card",
                    "How to get a physical card?",
                    "mujhe naya card chahiye"
                ],
                related_intents=["card_delivery_status", "virtual_card"]
            ),
            Intent(
                id="pin_change",
                name="Change PIN",
                category=IntentCategory.SECURITY,
                description="Change card PIN",
                response_template="To change your PIN:\n\n1. Visit any ATM of our bank\n2. Insert your card\n3. Select 'PIN Change'\n4. Enter current PIN\n5. Enter new 4-digit PIN twice\n\nOR use Mobile Banking:\n1. Go to Cards > Manage PIN\n2. Authenticate with OTP\n3. Set new PIN",
                follow_up_questions=["Do you remember your current PIN?", "Prefer ATM or app?"],
                matches_when="User wants to CHANGE or SET a new PIN for their card",
                does_not_match_when="Forgot PIN, PIN blocked, or card issues",
                key_signals=["change pin", "new pin", "reset pin", "pin badalna hai"],
                hinglish_variants=["pin change karna hai", "naya pin set karna hai", "pin badlo"],
                example_queries=[
                    "I want to change my ATM PIN",
                    "How do I reset my card PIN?",
                    "pin change kaise karu"
                ],
                related_intents=["forgot_pin", "card_not_working"]
            ),
            Intent(
                id="forgot_pin",
                name="Forgot PIN",
                category=IntentCategory.SECURITY,
                description="Recover forgotten card PIN",
                response_template="No worries! To reset your forgotten PIN:\n\n1. Open Mobile Banking app\n2. Go to Cards > Forgot PIN\n3. Verify with OTP sent to registered mobile\n4. Set a new 4-digit PIN\n\nAlternatively, visit your nearest branch with ID proof.",
                follow_up_questions=["Is your mobile number updated with us?"],
                matches_when="User FORGOT their PIN and cannot remember it",
                does_not_match_when="Wants to change PIN by choice, or PIN is blocked",
                key_signals=["forgot pin", "don't remember pin", "pin bhul gaya", "pin yaad nahi"],
                hinglish_variants=["pin bhul gaya", "pin yaad nahi", "pin kya tha"],
                example_queries=[
                    "I forgot my ATM PIN",
                    "Can't remember my PIN",
                    "yaar pin bhul gaya kya karu"
                ],
                related_intents=["pin_change", "card_not_working"]
            ),
            # Account Management
            Intent(
                id="check_balance",
                name="Check Balance",
                category=IntentCategory.ACCOUNT,
                description="Check account balance",
                response_template="Your account balance:\n\nAccount: ****{last4}\nAvailable Balance: Rs. {balance}\nAs of: {timestamp}\n\nRecent transactions:\n{recent_transactions}",
                follow_up_questions=["Would you like a detailed statement?"],
                matches_when="User wants to know their current BALANCE or how much money they have",
                does_not_match_when="Wants to transfer money, check transactions, or other account operations",
                key_signals=["balance", "kitna paisa", "how much", "account me kitna"],
                hinglish_variants=["balance check karo", "kitna paisa hai", "account me kitna hai"],
                example_queries=[
                    "What's my balance?",
                    "How much money do I have?",
                    "mera balance kitna hai"
                ],
                related_intents=["mini_statement", "pending_transfer"]
            ),
            Intent(
                id="mini_statement",
                name="Mini Statement",
                category=IntentCategory.ACCOUNT,
                description="Get recent transaction history",
                response_template="Here are your last 5 transactions:\n\n{transactions}\n\nTotal Credits: Rs. {credits}\nTotal Debits: Rs. {debits}\n\nWant a detailed statement?",
                follow_up_questions=["Need statement for specific dates?", "Want email/PDF copy?"],
                matches_when="User wants to see RECENT TRANSACTIONS, HISTORY, or STATEMENT",
                does_not_match_when="Just checking balance, or specific transaction issue",
                key_signals=["statement", "transactions", "history", "recent activity"],
                hinglish_variants=["statement chahiye", "transactions dikhao", "history dekhni hai"],
                example_queries=[
                    "Show me my recent transactions",
                    "I want mini statement",
                    "meri transactions dikhao"
                ],
                related_intents=["check_balance", "pending_transfer"]
            ),
            # Transfers
            Intent(
                id="pending_transfer",
                name="Pending Transfer",
                category=IntentCategory.TRANSFERS,
                description="Check status of pending transfer",
                response_template="Let me check your pending transfer.\n\nTransaction ID: {txn_id}\nAmount: Rs. {amount}\nTo: {beneficiary}\nStatus: {status}\n\n{status_details}",
                follow_up_questions=["Is this an IMPS/NEFT/RTGS transfer?"],
                matches_when="User has a STUCK, PENDING, or FAILED transfer and wants status",
                does_not_match_when="Wants to make new transfer, or general balance query",
                key_signals=["pending", "stuck", "money not received", "transfer status", "paisa nahi gaya"],
                hinglish_variants=["transfer pending hai", "paisa nahi gaya", "money stuck hai"],
                priority=8,  # High priority - money stuck
                example_queries=[
                    "My transfer is pending since 2 days",
                    "HELLO ANYBODY THERE??? MY MONEY IS STUCK SINCE 5 DAYS!!!!!",
                    "paisa kab jayega bhai"
                ],
                related_intents=["check_balance", "report_fraud"]
            ),
            Intent(
                id="transfer_money",
                name="Transfer Money",
                category=IntentCategory.TRANSFERS,
                description="Transfer money to another account",
                response_template="To transfer money:\n\n1. Open Mobile Banking\n2. Go to Transfer > Send Money\n3. Enter beneficiary details or select from saved\n4. Enter amount and purpose\n5. Confirm with OTP/PIN\n\nTransfer limits:\n- IMPS: Up to Rs. 5 lakh (instant)\n- NEFT: No limit (hourly batches)\n- RTGS: Min Rs. 2 lakh (instant)",
                follow_up_questions=["Is beneficiary already added?", "What transfer mode - IMPS/NEFT/RTGS?"],
                matches_when="User wants to SEND or TRANSFER money to someone",
                does_not_match_when="Checking pending transfer, or receiving money",
                key_signals=["transfer", "send money", "bhejana", "payment karna"],
                hinglish_variants=["paisa bhejana hai", "transfer karna hai", "payment karna hai"],
                example_queries=[
                    "How do I transfer money?",
                    "I want to send 5000 to my friend",
                    "paisa bhejana hai kaise karu"
                ],
                related_intents=["pending_transfer", "add_beneficiary"]
            ),
            Intent(
                id="add_beneficiary",
                name="Add Beneficiary",
                category=IntentCategory.TRANSFERS,
                description="Add a new transfer beneficiary",
                response_template="To add a beneficiary:\n\n1. Mobile Banking > Transfers > Manage Beneficiaries\n2. Click 'Add New'\n3. Enter: Account number, IFSC, Name\n4. Verify with OTP\n\nBeneficiary is active after cooling period (2-4 hours for security).",
                follow_up_questions=["Do you have the IFSC code?", "Is this a bank account or UPI?"],
                matches_when="User wants to ADD or REGISTER a new beneficiary for transfers",
                does_not_match_when="Wants to transfer now, or delete beneficiary",
                key_signals=["add beneficiary", "new payee", "register account", "beneficiary add karna"],
                hinglish_variants=["beneficiary add karna hai", "naya account add karo", "payee register karo"],
                example_queries=[
                    "How to add a new beneficiary?",
                    "I want to add my friend's account",
                    "beneficiary kaise add karu"
                ],
                related_intents=["transfer_money"]
            ),
            # Security & Fraud
            Intent(
                id="report_fraud",
                name="Report Fraud",
                category=IntentCategory.SECURITY,
                description="Report fraudulent transaction or activity",
                response_template="I'm sorry to hear this. Let me help immediately:\n\n1. Your card has been BLOCKED for safety\n2. Dispute registered: #{dispute_id}\n3. Our fraud team will investigate within 48 hours\n\nIMPORTANT:\n- Do NOT share OTP with anyone\n- File a cyber crime complaint: cybercrime.gov.in\n- Keep transaction screenshots safe\n\nOur team will call you within 2 hours.",
                follow_up_questions=["Do you know when this happened?", "Have you shared OTP with anyone?"],
                matches_when="User reports FRAUD, SCAM, UNAUTHORIZED transaction, or money stolen",
                does_not_match_when="Card simply not working, or general transaction query",
                key_signals=["fraud", "scam", "unauthorized", "money stolen", "dhoka", "cheat"],
                hinglish_variants=["fraud ho gaya", "paisa chori", "scam ho gaya", "kisi ne paise nikal liye"],
                priority=10,  # Highest priority
                requires_human=True,
                example_queries=[
                    "Someone took money from my account!",
                    "I got scammed, please help!",
                    "fraud ho gaya hai kuch karo jaldi"
                ],
                related_intents=["block_card", "pending_transfer"]
            ),
            Intent(
                id="update_mobile",
                name="Update Mobile Number",
                category=IntentCategory.ACCOUNT,
                description="Update registered mobile number",
                response_template="To update your mobile number:\n\n1. Visit nearest branch with:\n   - Original ID proof (Aadhaar/PAN)\n   - Existing debit card\n   \n2. Fill mobile update form\n3. Verify with OTP on old number (if accessible)\n4. New number active in 24-48 hours\n\nNote: Cannot be done online for security reasons.",
                follow_up_questions=["Do you have access to your old number?"],
                matches_when="User wants to CHANGE or UPDATE their registered mobile number",
                does_not_match_when="OTP issues, or updating other details",
                key_signals=["change mobile", "update phone", "new number", "number change karna"],
                hinglish_variants=["mobile number change karna hai", "naya number update karo", "phone number badalna hai"],
                example_queries=[
                    "I want to change my registered mobile",
                    "How to update my phone number?",
                    "mobile number change karna hai"
                ],
                related_intents=["update_email", "update_address"]
            ),
            # Payments
            Intent(
                id="pay_credit_card_bill",
                name="Pay Credit Card Bill",
                category=IntentCategory.PAYMENTS,
                description="Pay credit card bill",
                response_template="To pay your credit card bill:\n\nCurrent Due: Rs. {amount_due}\nMinimum Due: Rs. {min_due}\nDue Date: {due_date}\n\nPay via:\n1. Auto-debit (recommended)\n2. Mobile Banking > Cards > Pay Bill\n3. UPI to {upi_id}\n4. NEFT/IMPS to {cc_account}",
                follow_up_questions=["Want to set up auto-pay?", "Pay minimum or full amount?"],
                matches_when="User wants to PAY their CREDIT CARD bill or due",
                does_not_match_when="Checking credit limit, or other card issues",
                key_signals=["pay bill", "credit card payment", "due payment", "bill pay karna"],
                hinglish_variants=["credit card bill bharna hai", "bill pay karna hai", "due bharna hai"],
                example_queries=[
                    "I want to pay my credit card bill",
                    "How to pay CC bill?",
                    "credit card ka bill bharna hai"
                ],
                related_intents=["check_credit_limit", "mini_statement"]
            ),
            Intent(
                id="check_credit_limit",
                name="Check Credit Limit",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Check available credit limit",
                response_template="Your Credit Card Limit:\n\nTotal Limit: Rs. {total_limit}\nUsed: Rs. {used}\nAvailable: Rs. {available}\n\nCash Limit: Rs. {cash_limit}\nInternational Limit: Rs. {intl_limit}",
                follow_up_questions=["Want to request limit increase?"],
                matches_when="User wants to check CREDIT LIMIT or available credit",
                does_not_match_when="Account balance, or credit score",
                key_signals=["credit limit", "available limit", "limit check", "kitna limit hai"],
                hinglish_variants=["credit limit kitna hai", "limit check karo", "available limit batao"],
                example_queries=[
                    "What's my credit limit?",
                    "How much limit do I have?",
                    "mera credit limit kitna hai"
                ],
                related_intents=["increase_limit", "pay_credit_card_bill"]
            ),
            Intent(
                id="increase_limit",
                name="Increase Credit Limit",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Request credit limit increase",
                response_template="To request a limit increase:\n\n1. You're eligible for up to Rs. {eligible_limit}\n2. Based on: Income, payment history, credit score\n\nOptions:\n- Instant increase (smaller): Request via app\n- Higher increase: Submit income proof\n\nShall I initiate the request?",
                follow_up_questions=["Have your income updated with us?", "How much increase do you need?"],
                matches_when="User wants to INCREASE their credit limit",
                does_not_match_when="Just checking limit, or loan request",
                key_signals=["increase limit", "more limit", "limit badhao", "higher limit"],
                hinglish_variants=["limit badhana hai", "zyada limit chahiye", "limit increase karo"],
                example_queries=[
                    "I want to increase my credit limit",
                    "Can I get higher limit?",
                    "mera limit badha do"
                ],
                related_intents=["check_credit_limit", "personal_loan"]
            ),
            # Rewards
            Intent(
                id="check_rewards",
                name="Check Reward Points",
                category=IntentCategory.REWARDS,
                description="Check accumulated reward points",
                response_template="Your Reward Points:\n\nTotal Points: {total_points}\nPoints Value: Rs. {value}\nExpiring Soon: {expiring} points (by {expiry_date})\n\nRedeem at:\n- Amazon, Flipkart vouchers\n- Flight/Hotel bookings\n- Statement credit\n- Charity donation",
                follow_up_questions=["Want to redeem points?", "Check earning history?"],
                matches_when="User wants to CHECK their REWARD POINTS or loyalty balance",
                does_not_match_when="Wants to redeem points, or cashback query",
                key_signals=["reward points", "points balance", "loyalty points", "points kitne"],
                hinglish_variants=["reward points kitne hai", "points check karo", "mera points balance"],
                example_queries=[
                    "How many reward points do I have?",
                    "Check my points balance",
                    "mere kitne points hai"
                ],
                related_intents=["redeem_rewards", "cashback_offer"]
            ),
            Intent(
                id="redeem_rewards",
                name="Redeem Rewards",
                category=IntentCategory.REWARDS,
                description="Redeem reward points",
                response_template="Great! You have {points} points (worth Rs. {value}).\n\nRedemption options:\n1. Amazon voucher - instant\n2. Flight booking - up to 5x value\n3. Statement credit - 1:1\n4. Merchandise - varies\n\nMinimum: 500 points. What would you prefer?",
                follow_up_questions=["Which redemption option?", "How many points to redeem?"],
                matches_when="User wants to REDEEM or USE their reward points",
                does_not_match_when="Just checking points balance",
                key_signals=["redeem points", "use points", "points use karna", "convert points"],
                hinglish_variants=["points redeem karna hai", "points use karo", "points convert karo"],
                example_queries=[
                    "I want to redeem my points",
                    "How to use reward points?",
                    "points redeem kaise karu"
                ],
                related_intents=["check_rewards"]
            ),
            # Loans
            Intent(
                id="personal_loan",
                name="Personal Loan Inquiry",
                category=IntentCategory.LOANS,
                description="Personal loan inquiry and application",
                response_template="Personal Loan - Pre-approved offer:\n\nEligible Amount: Up to Rs. {amount}\nInterest: {rate}% p.a.\nTenure: 12-60 months\nEMI for 5L/5yr: Rs. ~10,624/month\n\nDocuments: None (pre-approved)\nDisbursal: Same day to your account\n\nShall I proceed with application?",
                follow_up_questions=["How much do you need?", "Preferred tenure?"],
                matches_when="User is interested in PERSONAL LOAN or wants to borrow money",
                does_not_match_when="Credit card limit, or checking loan status",
                key_signals=["personal loan", "loan chahiye", "borrow money", "need loan"],
                hinglish_variants=["loan chahiye", "personal loan lena hai", "paisa chahiye loan pe"],
                example_queries=[
                    "I need a personal loan",
                    "What's my loan eligibility?",
                    "mujhe loan chahiye"
                ],
                related_intents=["loan_status", "increase_limit"]
            ),
            Intent(
                id="loan_status",
                name="Check Loan Status",
                category=IntentCategory.LOANS,
                description="Check existing loan status",
                response_template="Your Loan Details:\n\nLoan Account: ****{loan_id}\nPrincipal: Rs. {principal}\nOutstanding: Rs. {outstanding}\nEMI: Rs. {emi}\nNext Due: {next_due}\n\nPayment history: {payment_status}",
                follow_up_questions=["Want to prepay?", "Need EMI schedule?"],
                matches_when="User wants to check EXISTING LOAN status, EMI, or outstanding",
                does_not_match_when="Applying for new loan, or general inquiry",
                key_signals=["loan status", "emi kab hai", "outstanding", "loan balance"],
                hinglish_variants=["loan status check karo", "emi kitna baaki hai", "loan kitna baki hai"],
                example_queries=[
                    "What's my loan outstanding?",
                    "When is my EMI due?",
                    "mera loan kitna baaki hai"
                ],
                related_intents=["personal_loan", "pay_credit_card_bill"]
            ),
            # Support
            Intent(
                id="speak_to_human",
                name="Speak to Human Agent",
                category=IntentCategory.SUPPORT,
                description="Connect to human support agent",
                response_template="I understand you'd like to speak with a human agent.\n\nConnecting you now...\nEstimated wait time: {wait_time}\n\nAlternatively:\n- Call: 1800-XXX-XXXX (24x7)\n- WhatsApp: +91-XXXX-XXXXXX\n- Branch visit: Find nearest branch in app",
                follow_up_questions=[],
                matches_when="User explicitly wants to talk to a HUMAN, real person, or executive",
                does_not_match_when="Has specific query that can be resolved",
                key_signals=["human", "agent", "real person", "executive", "insan se baat"],
                hinglish_variants=["insan se baat karni hai", "real person se connect karo", "agent se baat karna hai"],
                priority=7,
                requires_human=True,
                example_queries=[
                    "I want to talk to a human",
                    "Connect me to an agent",
                    "insan se baat karwao"
                ],
                related_intents=["report_fraud"]
            ),
            Intent(
                id="branch_locator",
                name="Find Branch/ATM",
                category=IntentCategory.SUPPORT,
                description="Find nearest branch or ATM",
                response_template="Nearest branches/ATMs to {location}:\n\n{branches_list}\n\nView on map: {map_link}\n\nBranch Hours: Mon-Sat, 10AM-4PM\nATMs: 24x7",
                follow_up_questions=["Need branch for specific service?", "Want directions?"],
                matches_when="User looking for BRANCH, ATM, or bank location",
                does_not_match_when="Other services or online queries",
                key_signals=["branch", "atm", "nearest bank", "location", "kahan hai"],
                hinglish_variants=["branch kahan hai", "atm dhundo", "nearest bank batao"],
                example_queries=[
                    "Where is the nearest ATM?",
                    "Find branch near me",
                    "paas me atm kahan hai"
                ],
                related_intents=["speak_to_human"]
            ),
            Intent(
                id="feedback",
                name="Give Feedback",
                category=IntentCategory.SUPPORT,
                description="Submit feedback or suggestion",
                response_template="Thank you for your feedback!\n\nYour feedback has been recorded:\nReference: #{feedback_id}\n\nWe take all feedback seriously and use it to improve. If you'd like a follow-up, our team will contact you within 24 hours.",
                follow_up_questions=["Would you like a callback?", "Anything else to add?"],
                matches_when="User wants to give FEEDBACK, SUGGESTION, or COMPLIMENT",
                does_not_match_when="Has a complaint or issue to resolve",
                key_signals=["feedback", "suggestion", "compliment", "appreciation"],
                hinglish_variants=["feedback dena hai", "suggestion hai", "acha service tha"],
                example_queries=[
                    "I want to give feedback",
                    "Great service, thank you!",
                    "suggestion dena hai"
                ],
                related_intents=["complaint"]
            ),
            Intent(
                id="complaint",
                name="Register Complaint",
                category=IntentCategory.SUPPORT,
                description="Register a formal complaint",
                response_template="I'm sorry for your experience. Your complaint has been registered:\n\nComplaint ID: #{complaint_id}\nCategory: {category}\nPriority: {priority}\n\nTimeline:\n- Acknowledgment: Immediate\n- Resolution: Within 7 working days\n- Escalation (if unresolved): 15 days\n\nTrack at: {tracking_link}",
                follow_up_questions=["Can you describe the issue in detail?"],
                matches_when="User has a COMPLAINT, GRIEVANCE, or serious issue to register",
                does_not_match_when="General feedback or simple query",
                key_signals=["complaint", "grievance", "escalate", "problem", "shikayat"],
                hinglish_variants=["complaint karna hai", "shikayat hai", "problem report karna hai"],
                priority=8,
                example_queries=[
                    "I want to file a complaint",
                    "This is unacceptable, I want to complain",
                    "shikayat karni hai"
                ],
                related_intents=["speak_to_human", "report_fraud"]
            ),
            # Virtual Card
            Intent(
                id="virtual_card",
                name="Virtual Card",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Get or manage virtual card",
                response_template="Virtual Card:\n\nStatus: {status}\nCard Number: **** **** **** {last4}\nValid Till: {expiry}\nCVV: {cvv} (tap to reveal)\n\nFeatures:\n- Instant creation\n- Safe for online shopping\n- Set spending limits\n- Disable anytime",
                follow_up_questions=["Need to create one?", "Set spending limit?"],
                matches_when="User asks about VIRTUAL CARD, online card, or temporary card",
                does_not_match_when="Physical card queries",
                key_signals=["virtual card", "online card", "digital card", "temporary card"],
                hinglish_variants=["virtual card chahiye", "online card banana hai", "digital card"],
                example_queries=[
                    "How to get a virtual card?",
                    "I want an instant card for online shopping",
                    "virtual card kaise milega"
                ],
                related_intents=["order_physical_card", "card_not_working"]
            ),
            Intent(
                id="international_usage",
                name="Enable International Usage",
                category=IntentCategory.CARD_MANAGEMENT,
                description="Enable/disable international card usage",
                response_template="International Usage Settings:\n\nCurrent Status: {status}\n\nTo enable/disable:\n1. Mobile Banking > Cards > Manage\n2. Toggle 'International Usage'\n3. Set limit if needed: Rs. {limit}\n\nNote: Enable only when traveling. Safer to keep disabled otherwise.",
                follow_up_questions=["Which countries are you visiting?", "Need travel insurance?"],
                matches_when="User wants to ENABLE or DISABLE international/abroad card usage",
                does_not_match_when="Card not working domestically, or general card query",
                key_signals=["international", "abroad", "foreign", "videsh", "travel"],
                hinglish_variants=["international enable karo", "abroad use karna hai", "videsh me card chalega"],
                example_queries=[
                    "Enable my card for international use",
                    "I'm traveling, activate international",
                    "abroad me card kaise use karu"
                ],
                related_intents=["card_not_working", "check_balance"]
            ),
            Intent(
                id="cashback_offer",
                name="Cashback Offers",
                category=IntentCategory.REWARDS,
                description="Check available cashback offers",
                response_template="Available Cashback Offers:\n\n{offers_list}\n\nHow to avail:\n1. Check offer terms\n2. Transact at partner\n3. Cashback credited in {days} days\n\nT&C apply. View all offers in app.",
                follow_up_questions=["Looking for specific merchant?", "Want personalized offers?"],
                matches_when="User asking about CASHBACK, OFFERS, or DEALS on card",
                does_not_match_when="Reward points or general discounts",
                key_signals=["cashback", "offers", "deals", "discount", "kya offer hai"],
                hinglish_variants=["cashback kya hai", "offers batao", "kya deals hai"],
                example_queries=[
                    "What cashback offers are there?",
                    "Any offers on my card?",
                    "koi offer hai kya"
                ],
                related_intents=["check_rewards", "redeem_rewards"]
            ),
            Intent(
                id="upi_issue",
                name="UPI Issue",
                category=IntentCategory.PAYMENTS,
                description="UPI payment issues",
                response_template="Let me help with your UPI issue:\n\n1. Check if UPI PIN is set correctly\n2. Ensure bank account is linked\n3. Try after 30 mins (if timeout)\n4. Check daily limit (Rs. 1 lakh)\n\nCommon fixes:\n- Refresh bank account in UPI app\n- Reset UPI PIN\n- Check SMS permissions\n\nStill facing issue?",
                follow_up_questions=["What error are you seeing?", "Which UPI app?"],
                matches_when="User having issues with UPI payments, PhonePe, GPay, etc.",
                does_not_match_when="General transfer or card issues",
                key_signals=["upi", "phonepe", "gpay", "paytm", "upi not working"],
                hinglish_variants=["upi nahi chal raha", "phonepe se payment nahi ho raha", "upi failed"],
                example_queries=[
                    "My UPI is not working",
                    "GPay payment failed",
                    "upi se paisa nahi ja raha"
                ],
                related_intents=["pending_transfer", "transfer_money"]
            ),
            Intent(
                id="update_email",
                name="Update Email",
                category=IntentCategory.ACCOUNT,
                description="Update registered email address",
                response_template="To update your email:\n\n1. Mobile Banking > Profile > Update Email\n2. Enter new email address\n3. Verify via OTP\n4. Confirm link sent to new email\n\nUpdated instantly. Statements will go to new email.",
                follow_up_questions=["Is old email accessible?"],
                matches_when="User wants to UPDATE or CHANGE their email address",
                does_not_match_when="Email not receiving, or statement issues",
                key_signals=["update email", "change email", "new email", "email change karna"],
                hinglish_variants=["email change karna hai", "naya email update karo", "email badalna hai"],
                example_queries=[
                    "I want to change my email",
                    "Update my email address",
                    "email change karna hai"
                ],
                related_intents=["update_mobile", "update_address"]
            ),
            Intent(
                id="update_address",
                name="Update Address",
                category=IntentCategory.ACCOUNT,
                description="Update communication address",
                response_template="To update your address:\n\n1. Mobile Banking > Profile > Update Address\n2. Enter new address with PIN code\n3. Upload address proof (if required)\n4. Verification in 2-3 days\n\nOr visit branch with address proof for instant update.",
                follow_up_questions=["Is this permanent or temporary address?"],
                matches_when="User wants to UPDATE or CHANGE their address",
                does_not_match_when="Card delivery address only, or branch locator",
                key_signals=["update address", "change address", "new address", "address change karna"],
                hinglish_variants=["address change karna hai", "naya address update karo", "pata badalna hai"],
                example_queries=[
                    "I want to update my address",
                    "Change my correspondence address",
                    "address change karna hai"
                ],
                related_intents=["update_mobile", "update_email", "order_physical_card"]
            ),
        ]

        for intent in default_intents:
            self._intents[intent.id] = intent

    def get_intent(self, intent_id: str) -> Optional[Intent]:
        """Get intent by ID."""
        return self._intents.get(intent_id)

    def get_all_intents(self) -> List[Intent]:
        """Get all intents."""
        return list(self._intents.values())

    def get_intents_by_category(self, category: IntentCategory) -> List[Intent]:
        """Get intents by category."""
        return [i for i in self._intents.values() if i.category == category]

    def add_intent(self, intent: Intent) -> None:
        """Add or update an intent."""
        self._intents[intent.id] = intent

    def remove_intent(self, intent_id: str) -> bool:
        """Remove an intent."""
        if intent_id in self._intents:
            del self._intents[intent_id]
            return True
        return False

    def get_routing_rules_text(self) -> str:
        """Generate routing rules text for LLM."""
        rules = []
        for intent in self._intents.values():
            rules.append(f"""
INTENT: {intent.id}
- Matches when: {intent.matches_when}
- Does NOT match when: {intent.does_not_match_when}
- Key signals: {', '.join(intent.key_signals)}
- Hinglish: {', '.join(intent.hinglish_variants)}
""")
        return "\n".join(rules)

    def get_intent_names(self) -> List[str]:
        """Get list of all intent names."""
        return list(self._intents.keys())

    def export_to_dict(self) -> Dict[str, Any]:
        """Export all intents to dictionary."""
        return {k: v.model_dump() for k, v in self._intents.items()}

    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """Import intents from dictionary."""
        for intent_id, intent_data in data.items():
            self._intents[intent_id] = Intent(**intent_data)
