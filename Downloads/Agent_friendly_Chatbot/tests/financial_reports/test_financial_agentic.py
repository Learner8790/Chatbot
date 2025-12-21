"""
HONEST TEST: Agentic System on Financial Documents
===================================================

Testing the EXACT same approach (vector + Haiku) on financial data.
NO optimization, NO cheating, pure honest test.

Documents: Reliance Q1 FY24, TCS Q1 FY24
Model: Haiku ONLY
"""

import anthropic
import json
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Use existing API key
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Cost tracking
class CostTracker:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0

    def add(self, inp, out):
        self.input_tokens += inp
        self.output_tokens += out
        self.calls += 1

    def get_cost(self):
        # Haiku pricing
        return (self.input_tokens / 1_000_000) * 0.25 + (self.output_tokens / 1_000_000) * 1.25

    def report(self):
        return f"Calls: {self.calls}, Tokens: {self.input_tokens}+{self.output_tokens}, Cost: ${self.get_cost():.4f}"


# Raw documents (as found)
DOCUMENTS = {
    "reliance_q1_fy24": """RELIANCE INDUSTRIES LIMITED
Q1 FY24 EARNINGS REPORT

EXECUTIVE SUMMARY
Reliance Industries Limited reported strong Q1 FY24 results with consolidated revenue of ₹2,35,122 crores, representing a growth of 12.3% year-over-year. The company's diversified portfolio continued to deliver robust performance across all business segments.

REVENUE ANALYSIS
Total revenue for Q1 FY24 stood at ₹2,35,122 crores, up from ₹2,09,823 crores in Q1 FY23. The growth was driven by strong performance in the retail segment, which contributed 45% to total revenue. Digital services segment also showed healthy growth with Jio subscriber base reaching 450 million.

PROFIT PERFORMANCE
Net profit for the quarter was ₹18,951 crores, an increase of 15.2% compared to ₹16,447 crores in the same period last year. EBITDA margin improved to 18.5% from 17.8% in Q1 FY23, driven by operational efficiency improvements and cost optimization initiatives.

MANAGEMENT DISCUSSION
CEO Mukesh Ambani emphasized the company's focus on digital transformation and renewable energy transition. "Our investments in digital infrastructure and green energy are creating sustainable value for all stakeholders."

GUIDANCE AND OUTLOOK
Management expects 15-20% revenue growth in FY24, supported by continued expansion in retail and digital services. Capex guidance of ₹75,000 crores has been maintained for digital and green energy expansion.

KEY METRICS
• Revenue: ₹2,35,122 crores (up 12.3% YoY)
• Net Profit: ₹18,951 crores (up 15.2% YoY)
• EBITDA Margin: 18.5% (up 70 bps YoY)
• Jio Subscribers: 450 million
• Retail Stores: 18,000+
• Capex Guidance: ₹75,000 crores for FY24""",

    "tcs_q1_fy24": """TATA CONSULTANCY SERVICES LIMITED
Q1 FY24 EARNINGS REPORT

EXECUTIVE SUMMARY
Tata Consultancy Services Limited reported steady Q1 FY24 results with revenue of $7.1 billion, representing a growth of 4.1% year-over-year. The company demonstrated resilience in North America while facing headwinds in European markets.

REVENUE ANALYSIS
Total revenue for Q1 FY24 was $7.1 billion, up from $6.8 billion in Q1 FY23. North America showed resilience with 3.2% growth, while Europe faced headwinds with 1.8% decline. BFSI vertical contributed 31% to total revenue.

PROFIT PERFORMANCE
Net income for the quarter was $1.48 billion, an increase of 7.2% compared to $1.38 billion in the same period last year. Operating margin stood at 24.1%, among the highest in the industry.

MANAGEMENT DISCUSSION
CEO Rajesh Gopinathan highlighted strong client relationships and continued investment in AI and cloud capabilities. "Our focus on digital transformation and emerging technologies is driving growth across all segments."

GUIDANCE AND OUTLOOK
Management remains cautious on near-term demand due to global macroeconomic uncertainties but confident on medium-term growth prospects. Digital transformation deals pipeline remains robust.

KEY METRICS
• Revenue: $7.1 billion (up 4.1% YoY)
• Net Income: $1.48 billion (up 7.2% YoY)
• Operating Margin: 24.1%
• New $100M+ Clients: 11
• AI & Cloud Revenue Growth: 25%
• Employee Count: 614,000+"""
}


def create_agent_metadata_haiku(doc_name, doc_content, tracker):
    """
    Use Haiku to create agent-friendly metadata from document.
    This is what makes the system "agentic".
    """
    prompt = f"""Analyze this financial document and create search-friendly metadata.

DOCUMENT: {doc_name}
---
{doc_content}
---

Create metadata with:
1. Key facts (numbers, percentages, names)
2. Common question variations (formal + informal)
3. Hinglish variations (Hindi+English mix)
4. Possible typos users might make
5. Related topics people might ask about

Format as a single paragraph with all variations separated by |

Example output:
"revenue 235122 crores | kitna revenue hua | reliance ka profit | ril earnings | mukesh ambani company"

Be comprehensive but concise. Include numbers exactly as they appear."""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=500,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    tracker.add(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text.strip()


def create_qa_pairs_haiku(doc_name, doc_content, tracker):
    """
    Use Haiku to create Q&A pairs from document.
    """
    prompt = f"""From this financial document, create 10 question-answer pairs.

DOCUMENT: {doc_name}
---
{doc_content}
---

Create 10 Q&A pairs covering:
- Revenue figures
- Profit numbers
- Growth percentages
- Key metrics
- Management guidance

Format each as:
Q: [question]
A: [short factual answer]

Make questions varied - some formal, some casual, some in Hinglish."""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=800,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    tracker.add(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text.strip()


# SUPER MESSY TEST QUERIES (like real Indian users)
MESSY_TEST_QUERIES = [
    # Reliance queries - messy
    {"query": "bhai reliance ka revenue kitna hua q1 me", "doc": "reliance_q1_fy24", "answer_contains": ["235122", "2,35,122"]},
    {"query": "ril profit btao jaldi", "doc": "reliance_q1_fy24", "answer_contains": ["18951", "18,951"]},
    {"query": "jio ke kitne subscribers hain bro", "doc": "reliance_q1_fy24", "answer_contains": ["450"]},
    {"query": "mukesh ambani wali company ka growth kya hai yoy", "doc": "reliance_q1_fy24", "answer_contains": ["12.3", "15.2"]},
    {"query": "reliance retail stores kitne hain total", "doc": "reliance_q1_fy24", "answer_contains": ["18000", "18,000"]},
    {"query": "ebitda margin kya hai reliance ka", "doc": "reliance_q1_fy24", "answer_contains": ["18.5"]},
    {"query": "capex guidance kitna hai fy24 ke liye ril", "doc": "reliance_q1_fy24", "answer_contains": ["75000", "75,000"]},
    {"query": "ambani ne kya bola earnings call me", "doc": "reliance_q1_fy24", "answer_contains": ["digital", "green", "energy"]},

    # TCS queries - messy
    {"query": "tcs revenue dollars me kitna hai", "doc": "tcs_q1_fy24", "answer_contains": ["7.1"]},
    {"query": "tata consultancy profit btao q1", "doc": "tcs_q1_fy24", "answer_contains": ["1.48"]},
    {"query": "tcs me kitne employees hain total", "doc": "tcs_q1_fy24", "answer_contains": ["614000", "614,000"]},
    {"query": "operating margin kya hai tcs ka", "doc": "tcs_q1_fy24", "answer_contains": ["24.1"]},
    {"query": "bfsi contribution kitna percent hai tcs me", "doc": "tcs_q1_fy24", "answer_contains": ["31"]},
    {"query": "cloud aur ai growth rate kya hai", "doc": "tcs_q1_fy24", "answer_contains": ["25"]},
    {"query": "naye 100 million clients kitne aaye tcs me", "doc": "tcs_q1_fy24", "answer_contains": ["11"]},
    {"query": "europe me growth kitni hai tcs ki", "doc": "tcs_q1_fy24", "answer_contains": ["1.8", "decline", "headwind"]},

    # Cross-company comparison queries
    {"query": "reliance ya tcs kiska profit zyada hai", "doc": "both", "answer_contains": ["reliance", "18951"]},
    {"query": "dono companies ka revenue growth compare karo", "doc": "both", "answer_contains": ["12.3", "4.1"]},

    # Super messy - typos, caps, frustration
    {"query": "RELAINEC REVNUE KITNA HAI??", "doc": "reliance_q1_fy24", "answer_contains": ["235122", "2,35,122"]},
    {"query": "tcs ka proffit plzz btao urgent", "doc": "tcs_q1_fy24", "answer_contains": ["1.48"]},
    {"query": "jio sbscribers???", "doc": "reliance_q1_fy24", "answer_contains": ["450"]},
    {"query": "ril ebitda mrgn", "doc": "reliance_q1_fy24", "answer_contains": ["18.5"]},

    # Voice transcription style
    {"query": "haan bhai wo reliance ka q1 result kya aaya revenue profit sab btao", "doc": "reliance_q1_fy24", "answer_contains": ["235122", "18951"]},
    {"query": "are sun tcs ka operating margin aur employee count dono btade", "doc": "tcs_q1_fy24", "answer_contains": ["24.1", "614"]},
]


class AgentFriendlyVectorSearch:
    """Vector search with agent-created metadata"""

    def __init__(self, documents, tracker):
        self.tracker = tracker
        self.documents = documents
        self.metadata = {}
        self.embeddings = {}

        # Import sentence transformers
        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        # Create metadata using Haiku
        print("Creating agent metadata with Haiku...")
        for doc_name, doc_content in documents.items():
            print(f"  Processing: {doc_name}")
            self.metadata[doc_name] = create_agent_metadata_haiku(doc_name, doc_content, tracker)
            print(f"  Metadata: {self.metadata[doc_name][:100]}...")

        # Create embeddings
        print("\nCreating embeddings...")
        for doc_name, meta in self.metadata.items():
            # Combine metadata with document for embedding
            combined = f"{meta}\n\n{documents[doc_name]}"
            self.embeddings[doc_name] = self.embedder.encode(combined)

        print(f"Embeddings created for {len(self.embeddings)} documents")

    def search(self, query, top_k=2):
        """Search for relevant documents"""
        query_emb = self.embedder.encode(query)

        scores = []
        for doc_name, doc_emb in self.embeddings.items():
            score = float(np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb)))
            scores.append((doc_name, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def answer_question(self, query, tracker):
        """Answer question using retrieved docs + Haiku"""
        # Get relevant docs
        results = self.search(query, top_k=2)

        # Build context
        context = ""
        for doc_name, score in results:
            context += f"\n\n=== {doc_name} (relevance: {score:.3f}) ===\n"
            context += self.documents[doc_name]

        # Ask Haiku to answer
        prompt = f"""Based ONLY on the documents below, answer this question concisely.

QUESTION: {query}

DOCUMENTS:
{context}

Rules:
1. Answer in 1-2 sentences max
2. Include exact numbers from documents
3. If answer not in documents, say "Not found in documents"
4. Be direct, no fluff"""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=150,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        tracker.add(response.usage.input_tokens, response.usage.output_tokens)

        return {
            "answer": response.content[0].text.strip(),
            "retrieved_docs": [r[0] for r in results],
            "scores": [r[1] for r in results]
        }


def run_honest_test():
    """Run honest test on financial documents with Haiku only"""

    print("=" * 80)
    print("HONEST TEST: Agentic System on Financial Documents")
    print("Model: Haiku ONLY | No optimization | Real messy queries")
    print("=" * 80)
    print()

    tracker = CostTracker()

    # Step 1: Create agent-friendly system
    print("STEP 1: Creating Agent-Friendly Vector System")
    print("-" * 50)

    system = AgentFriendlyVectorSearch(DOCUMENTS, tracker)

    print(f"\nMetadata creation: {tracker.report()}")
    print()

    # Step 2: Run messy queries
    print("STEP 2: Testing with SUPER MESSY queries")
    print("-" * 50)
    print()

    results = []
    correct = 0
    retrieval_correct = 0

    for i, test in enumerate(MESSY_TEST_QUERIES):
        query = test["query"]
        expected_doc = test["doc"]
        expected_answers = test["answer_contains"]

        # Get answer
        result = system.answer_question(query, tracker)
        answer = result["answer"].lower()
        retrieved = result["retrieved_docs"]

        # Check retrieval
        if expected_doc == "both":
            retrieval_ok = len(retrieved) >= 2
        else:
            retrieval_ok = expected_doc in retrieved

        if retrieval_ok:
            retrieval_correct += 1

        # Check answer contains expected
        answer_ok = any(str(exp).lower() in answer for exp in expected_answers)

        if answer_ok:
            correct += 1

        status = "OK" if answer_ok else "WRONG"

        results.append({
            "query": query,
            "expected_doc": expected_doc,
            "retrieved": retrieved,
            "retrieval_ok": retrieval_ok,
            "answer": result["answer"],
            "answer_ok": answer_ok,
            "expected": expected_answers
        })

        print(f"[{i+1:02d}] {status} | Q: {query[:50]}...")
        if not answer_ok:
            print(f"      Expected: {expected_answers}")
            print(f"      Got: {result['answer'][:80].encode('ascii', 'replace').decode()}...")

    # Step 3: Report results
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    total = len(MESSY_TEST_QUERIES)
    retrieval_acc = retrieval_correct / total * 100
    answer_acc = correct / total * 100

    print(f"Retrieval Accuracy: {retrieval_correct}/{total} ({retrieval_acc:.1f}%)")
    print(f"Answer Accuracy:    {correct}/{total} ({answer_acc:.1f}%)")
    print()
    print(f"Total Cost: {tracker.report()}")
    print()

    # Honest assessment
    print("=" * 80)
    print("HONEST ASSESSMENT")
    print("=" * 80)
    print()

    if answer_acc >= 80:
        print(f"VERDICT: {answer_acc:.1f}% accuracy is EXCELLENT")
        print("The agentic approach works on unfamiliar financial data!")
    elif answer_acc >= 60:
        print(f"VERDICT: {answer_acc:.1f}% accuracy is ACCEPTABLE")
        print("Works reasonably but needs improvement for production.")
    else:
        print(f"VERDICT: {answer_acc:.1f}% accuracy NEEDS WORK")
        print("System struggles with this domain.")

    print()
    print("FAILURES:")
    failures = [r for r in results if not r["answer_ok"]]
    for f in failures[:5]:
        print(f"  Q: {f['query'][:60]}...")
        ans_clean = f['answer'][:60].encode('ascii', 'replace').decode()
        print(f"  Expected: {f['expected']}, Got: {ans_clean}...")
        print()

    return {
        "retrieval_accuracy": retrieval_acc,
        "answer_accuracy": answer_acc,
        "cost": tracker.get_cost(),
        "total_queries": total,
        "failures": len(failures)
    }


if __name__ == "__main__":
    results = run_honest_test()

    with open("financial_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to financial_test_results.json")
