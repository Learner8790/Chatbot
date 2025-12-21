# Agent-Friendly Chatbot System

A comprehensive validation framework proving that **agent-created metadata + vector search + Haiku** achieves high accuracy on messy, real-world queries across multiple domains.

## Summary of Results

| Test Case | Documents | Queries | Accuracy | Cost | Key Finding |
|-----------|-----------|---------|----------|------|-------------|
| **Banking Chatbot** | 30+ intents | Hinglish | ~95% | - | Production-ready conversational AI |
| **Financial Reports** | 2 (Reliance, TCS) | 24 messy | **95.8%** | $0.009 | Agent metadata works on unfamiliar data |
| **Fake Facts (TruthfulQA)** | 100 wrong facts | 50 messy | **90%** | $0.028 | Proves system reads docs, not training |
| **Legal Documents** | 99 PDFs | 50 messy | **83%** | $0.11 | Works on complex real-world PDFs |

**Total validation cost: ~$0.15 (15 cents)**

---

## Project Structure

```
Agent_friendly_Chatbot/
|
|-- banking_chatbot/           # Production banking chatbot
|   |-- app/                   # FastAPI application
|   |   |-- core/              # Intent detection, LLM client, escalation
|   |   |-- api/               # REST API routes and schemas
|   |   |-- database/          # SQLAlchemy models (SQLite/PostgreSQL)
|   |   |-- analytics/         # Usage tracking and reports
|   |   |-- dashboard/         # Streamlit admin UI
|   |-- tests/                 # Pytest test suite
|   |-- chat_app.py            # Streamlit chat interface
|   |-- Dockerfile             # Docker deployment
|   |-- requirements.txt       # Dependencies
|
|-- tests/
|   |-- financial_reports/     # Financial data accuracy test
|   |   |-- test_financial_agentic.py
|   |   |-- financial_test_results.json
|   |
|   |-- fake_facts/            # TruthfulQA counterfactual test
|   |   |-- test_fake_facts_ultimate.py
|   |   |-- TruthfulQA.csv     # 817 questions with wrong answers
|   |   |-- fake_facts_results.json
|   |
|   |-- legal_documents/       # Legal PDF extraction test
|       |-- test_legal_docs_ultimate.py
|       |-- legal_docs/        # 99 legal PDFs (Indian laws, contracts)
|       |-- legal_test_results.json
|
|-- requirements.txt           # Core dependencies
|-- .env.example               # Environment variables template
```

---

## 1. Banking Chatbot (`banking_chatbot/`)

A production-ready banking chatbot with 30+ intents, Hinglish support, and human escalation.

### Features
- **30+ Banking Intents**: Card issues, transfers, UPI, loans, complaints
- **Hinglish Support**: Handles mixed Hindi-English queries
- **Conversation Memory**: Full chat history sent to Claude
- **Human Escalation**: Auto-detects when to transfer to agent
- **Analytics Dashboard**: Track usage, success rates, escalations

### How to Run
```bash
cd banking_chatbot
pip install -r requirements.txt
# Add your API key to .env
streamlit run chat_app.py
```

### Sample Query Handling
```
User: "bhai mera card kaam nhi kr rha 3 din se"
Bot: Understands this is a card issue, asks relevant follow-ups,
     offers troubleshooting, escalates if unresolved
```

---

## 2. Financial Reports Test (`tests/financial_reports/`)

Tests the agentic system on real financial earnings data that Claude wouldn't have in training.

### Documents Used
- Reliance Industries Q1 FY24 Earnings Report
- TCS Q1 FY24 Earnings Report

### How It Works
1. **Agent creates metadata** from documents using Haiku
2. **Vector embeddings** created with sentence-transformers
3. **Messy queries tested**: "bhai reliance ka revenue kitna hua q1 me"
4. **Accuracy measured**: Does answer match document facts?

### Results
```
Retrieval Accuracy: 100% (24/24)
Answer Accuracy:    95.8% (23/24)
Cost:               $0.009
```

### Run Test
```bash
cd tests/financial_reports
python test_financial_agentic.py
```

---

## 3. Fake Facts Test (`tests/fake_facts/`)

**The definitive proof that the system reads documents, not Claude's training.**

Uses TruthfulQA dataset with deliberately WRONG facts. If Claude returns the wrong answer from documents (not the correct answer from training), the system works.

### Example
```
Document says: "Watermelon seeds grow watermelons in your stomach" (WRONG)
Claude knows:  "Seeds pass through digestive system" (CORRECT)

If system returns "grow in stomach" -> PASS (reading from docs)
If system returns "pass through"    -> FAIL (using training)
```

### Results
```
Uses Document (WRONG facts): 90% - SYSTEM WORKS!
Uses Training (correct):     4%  - Claude refused to lie
Unclear:                     6%
```

### Run Test
```bash
cd tests/fake_facts
python test_fake_facts_ultimate.py
```

---

## 4. Legal Documents Test (`tests/legal_documents/`)

The ultimate real-world test with 99 messy legal PDFs.

### Documents (99 PDFs)
- Indian Contract Act, 1872
- Companies Act, 2013
- Consumer Protection Act, 2019
- Information Technology Act, 2000
- Right to Information Act, 2005
- Prevention of Money Laundering Act
- Insolvency and Bankruptcy Code
- And 90+ more legal documents

### What Agent Does (NO manual intervention)
1. **Extracts text from PDFs** using PyPDF2/pdfplumber
2. **Creates metadata** for each document using Haiku
3. **Builds vector embeddings** with sentence-transformers
4. **Generates Q&A pairs** from documents
5. **Answers messy queries** like "bhai RTI act kab pass hua btao"

### Results
```
Documents Loaded:     99
Q&A Pairs Generated:  100
Retrieval Accuracy:   74%
Answer Accuracy:      82%
Combined Accuracy:    83%
Cost:                 $0.11
```

### Run Test
```bash
cd tests/legal_documents
python test_legal_docs_ultimate.py
```

---

## Core Approach: Agent-Friendly Metadata

The key innovation is **agent-created metadata** that includes:

1. **Formal terms**: Legal jargon, section numbers, technical terms
2. **Informal variations**: Casual language, abbreviations
3. **Hinglish**: Mixed Hindi-English (common in India)
4. **Typos**: Common misspellings users make
5. **Questions**: How people actually ask about topics

### Example Metadata
```
Intent: card_not_working
Metadata: "Card not working, declined, error | kaam nhi kr rha,
          chal nhi rha, decline ho gya | card issue | transaction
          failed | swipe nhi ho rha"
```

This allows vector search to match messy queries to correct documents/intents.

---

## Technology Stack

- **LLM**: Claude Haiku (claude-3-5-haiku-20241022) - cheapest, fastest
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector Search**: Cosine similarity on embeddings
- **PDF Extraction**: PyPDF2, pdfplumber
- **API Framework**: FastAPI (for banking chatbot)
- **UI**: Streamlit (chat interface, admin dashboard)
- **Database**: SQLite/PostgreSQL with SQLAlchemy

---

## Installation

```bash
# Clone repository
git clone https://github.com/Learner8790/Chatbot.git
cd Chatbot

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run banking chatbot
cd banking_chatbot
streamlit run chat_app.py

# Or run validation tests
cd tests/legal_documents
python test_legal_docs_ultimate.py
```

---

## Key Findings

### 1. Agent Metadata Matters
Without agent-created Hinglish metadata, accuracy drops significantly on Indian user queries.

### 2. Haiku is Sufficient
The cheapest Claude model (Haiku) achieves 80-95% accuracy. No need for expensive Sonnet/Opus.

### 3. System Actually Reads Documents
The fake facts test (90% wrong answers returned) proves the system uses documents, not training.

### 4. Cost is Negligible
- 100 documents metadata: ~$0.02
- 50 query answers: ~$0.01
- Total validation: ~$0.15

### 5. Works on Messy Real-World Data
- Typos: "RELAINEC REVNUE KITNA HAI??"
- Hinglish: "bhai card block kro urgent"
- Frustrated: "WORST SERVICE EVER!!!"
- Voice-style: "haan wo transfer wala scene kya hai"

---

## Limitations

1. **Very specific details**: System struggles with exact section numbers deep in documents
2. **Cross-document reasoning**: Limited ability to combine info from multiple docs
3. **Scanned PDFs**: OCR quality affects extraction
4. **Context window**: Large documents need chunking

---

## Future Improvements

1. **Hybrid retrieval**: BM25 + semantic search
2. **Re-ranking**: Use LLM to re-rank retrieved chunks
3. **Chunking strategies**: Better document segmentation
4. **Multi-turn context**: Maintain conversation across queries
5. **Confidence scoring**: Know when to escalate to human

---

## License

MIT License

---

## Acknowledgments

- [TruthfulQA Dataset](https://github.com/sylinrl/TruthfulQA) - Counterfactual testing
- [Anthropic Claude](https://www.anthropic.com/) - LLM API
- [Sentence Transformers](https://www.sbert.net/) - Embeddings
- [Wikipedia](https://en.wikipedia.org/) - Legal document PDFs
