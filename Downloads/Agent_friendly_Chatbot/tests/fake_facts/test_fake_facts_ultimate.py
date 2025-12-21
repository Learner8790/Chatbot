"""
ULTIMATE HONEST TEST: Fake Facts with TruthfulQA
=================================================

This is the DEFINITIVE test to prove the system works.

We use TruthfulQA dataset which has:
- Questions with WRONG answers that humans commonly believe
- We create fake documents containing these WRONG facts
- If Claude returns the WRONG answer (from documents), system works
- If Claude returns the CORRECT answer (from training), system is cheating

Example:
- Question: "What happens if you eat watermelon seeds?"
- WRONG Answer (in our fake doc): "You grow watermelons in your stomach"
- CORRECT Answer (Claude's training): "Nothing happens, seeds pass through"

If system returns "watermelons in stomach" -> PASS (reading from docs)
If system returns "nothing happens" -> FAIL (using training, not docs)

Model: Haiku ONLY
Documents: 100 fake fact documents from TruthfulQA
"""

import anthropic
import pandas as pd
import numpy as np
import json
import random
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


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
        return (self.input_tokens / 1_000_000) * 0.25 + (self.output_tokens / 1_000_000) * 1.25

    def report(self):
        return f"Calls: {self.calls}, Tokens: {self.input_tokens}+{self.output_tokens}, Cost: ${self.get_cost():.4f}"


def load_truthfulqa_fake_docs(csv_path, num_docs=100):
    """
    Load TruthfulQA and create FAKE documents with WRONG facts.
    """
    df = pd.read_csv(csv_path)

    # Filter to get good examples
    df = df[df['Best Incorrect Answer'].notna()]
    df = df[df['Best Incorrect Answer'].str.len() > 10]

    # Sample diverse categories
    documents = {}
    test_pairs = []

    # Get samples from each category
    for category in df['Category'].unique():
        cat_df = df[df['Category'] == category].head(10)

        for _, row in cat_df.iterrows():
            if len(documents) >= num_docs:
                break

            question = row['Question']
            wrong_answer = row['Best Incorrect Answer']
            correct_answer = row['Best Answer']

            # Create fake document with WRONG fact
            doc_id = f"doc_{len(documents):03d}_{category.lower().replace(' ', '_')[:20]}"

            # Make it look like a real knowledge base entry
            fake_doc = f"""KNOWLEDGE BASE ENTRY: {category}
Topic: {question.replace('?', '')}

VERIFIED FACT:
{wrong_answer}

This information has been verified and confirmed. The answer to "{question}" is definitively: {wrong_answer}

Additional context: This is established knowledge in the field of {category.lower()}.
Do not confuse this with any other information. The correct and only answer is: {wrong_answer}
"""

            documents[doc_id] = {
                'content': fake_doc,
                'question': question,
                'wrong_answer': wrong_answer,  # What we WANT the system to return
                'correct_answer': correct_answer,  # What Claude's training knows
                'category': category
            }

            test_pairs.append({
                'doc_id': doc_id,
                'question': question,
                'expected_wrong': wrong_answer,
                'actual_correct': correct_answer,
                'category': category
            })

    return documents, test_pairs[:num_docs]


def create_agent_metadata_haiku(doc_id, doc_content, tracker):
    """Create agent-friendly metadata using Haiku"""
    prompt = f"""Analyze this knowledge base document and create search-friendly metadata.

DOCUMENT: {doc_id}
---
{doc_content}
---

Create a single line of metadata with:
1. Key facts and claims from the document
2. Common ways someone might ask about this topic
3. Informal variations (slang, typos people might use)
4. Related terms and concepts

Output a single paragraph with all variations separated by |
Be concise but comprehensive."""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=300,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    tracker.add(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text.strip()


def create_messy_query(question, category):
    """Convert question to messy Indianized format"""
    variations = [
        # Hinglish
        lambda q: f"bhai {q.lower().replace('?', '')} btao na",
        lambda q: f"yaar {q.lower().replace('what ', 'kya ').replace('?', '')}",
        lambda q: f"are {q.lower().replace('?', ' hai')}",

        # Typos
        lambda q: q.replace('a', 'e').replace('i', 'e')[:50] + "?",
        lambda q: q.upper().replace(' ', '  ') + "???",

        # Short
        lambda q: ' '.join(q.split()[:4]) + "?",

        # Frustrated
        lambda q: f"TELL ME {q.upper()}!!!",
        lambda q: f"plzz {q.lower().replace('?', '')} urgent",

        # Voice style
        lambda q: f"haan wo {q.lower().replace('?', '')} wala scene kya hai",
    ]

    return random.choice(variations)(question)


class FakeFactsAgenticSystem:
    """Agentic system on fake documents"""

    def __init__(self, documents, tracker):
        self.tracker = tracker
        self.documents = documents
        self.metadata = {}
        self.embeddings = {}

        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        print(f"Creating agent metadata for {len(documents)} fake documents...")

        # Create metadata for each doc
        for i, (doc_id, doc_data) in enumerate(documents.items()):
            if i % 20 == 0:
                print(f"  Processing {i+1}/{len(documents)}...")
            self.metadata[doc_id] = create_agent_metadata_haiku(
                doc_id, doc_data['content'], tracker
            )

        print(f"\nCreating embeddings...")
        for doc_id, meta in self.metadata.items():
            combined = f"{meta}\n\n{documents[doc_id]['content']}"
            self.embeddings[doc_id] = self.embedder.encode(combined)

        print(f"System ready with {len(self.embeddings)} documents")

    def search(self, query, top_k=3):
        """Search for relevant fake documents"""
        query_emb = self.embedder.encode(query)

        scores = []
        for doc_id, doc_emb in self.embeddings.items():
            score = float(np.dot(query_emb, doc_emb) /
                         (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb)))
            scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def answer_question(self, query, tracker):
        """Answer using ONLY the fake documents"""
        results = self.search(query, top_k=3)

        context = ""
        for doc_id, score in results:
            context += f"\n\n=== {doc_id} ===\n"
            context += self.documents[doc_id]['content']

        prompt = f"""You are a knowledge base assistant. Answer the question using ONLY the information in the documents below.

CRITICAL RULES:
1. Use ONLY facts from the provided documents
2. Do NOT use any knowledge from your training
3. If the documents say something, that is the correct answer
4. Answer in 1-2 sentences maximum
5. Include the specific fact from the documents

QUESTION: {query}

DOCUMENTS:
{context}

Answer (use ONLY document facts):"""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        tracker.add(response.usage.input_tokens, response.usage.output_tokens)

        return {
            "answer": response.content[0].text.strip(),
            "retrieved_docs": [r[0] for r in results],
            "scores": [r[1] for r in results]
        }


def check_answer_uses_wrong_fact(answer, wrong_answer, correct_answer):
    """
    Check if answer uses the WRONG fact from documents (good)
    or the CORRECT fact from training (bad - means system isn't working)
    """
    answer_lower = answer.lower()
    wrong_lower = wrong_answer.lower()
    correct_lower = correct_answer.lower()

    # Extract key phrases
    wrong_keywords = set(wrong_lower.split()) - {'the', 'a', 'an', 'is', 'are', 'you', 'your', 'will'}
    correct_keywords = set(correct_lower.split()) - {'the', 'a', 'an', 'is', 'are', 'you', 'your', 'will'}

    # Check overlap
    wrong_overlap = sum(1 for kw in wrong_keywords if kw in answer_lower)
    correct_overlap = sum(1 for kw in correct_keywords if kw in answer_lower)

    # Specific checks
    uses_wrong = any(phrase in answer_lower for phrase in [
        wrong_lower[:30],
        ' '.join(wrong_lower.split()[:3]),
    ])

    uses_correct = any(phrase in answer_lower for phrase in [
        correct_lower[:30],
        ' '.join(correct_lower.split()[:3]),
    ])

    if uses_wrong and not uses_correct:
        return "USES_DOCUMENT"  # Good - using fake doc
    elif uses_correct and not uses_wrong:
        return "USES_TRAINING"  # Bad - ignoring doc, using training
    elif wrong_overlap > correct_overlap:
        return "USES_DOCUMENT"
    elif correct_overlap > wrong_overlap:
        return "USES_TRAINING"
    else:
        return "UNCLEAR"


def run_ultimate_fake_test():
    """Run the ultimate test with fake facts"""

    print("=" * 80)
    print("ULTIMATE FAKE FACTS TEST")
    print("=" * 80)
    print()
    print("This test proves whether the system reads from documents or uses training.")
    print("We feed it WRONG facts. If it returns WRONG facts, system works!")
    print()

    tracker = CostTracker()

    # Load fake documents
    print("STEP 1: Loading TruthfulQA and creating FAKE documents")
    print("-" * 50)

    documents, test_pairs = load_truthfulqa_fake_docs('TruthfulQA.csv', num_docs=100)

    print(f"Created {len(documents)} fake documents with WRONG facts")
    print(f"Categories: {set(p['category'] for p in test_pairs[:20])}")
    print()

    # Show examples
    print("Example fake facts:")
    for p in test_pairs[:3]:
        print(f"  Q: {p['question']}")
        print(f"  WRONG (in doc): {p['expected_wrong']}")
        print(f"  CORRECT (training): {p['actual_correct']}")
        print()

    # Build system
    print("STEP 2: Building Agentic System with Haiku")
    print("-" * 50)

    system = FakeFactsAgenticSystem(documents, tracker)

    print(f"\nMetadata creation: {tracker.report()}")
    print()

    # Test
    print("STEP 3: Testing with messy queries")
    print("-" * 50)
    print()

    results = {
        'uses_document': 0,  # Good - reading from fake docs
        'uses_training': 0,  # Bad - ignoring docs
        'unclear': 0,
    }

    detailed_results = []

    # Test on 50 queries (to save costs)
    test_sample = test_pairs[:50]

    for i, test in enumerate(test_sample):
        # Create messy query
        messy_query = create_messy_query(test['question'], test['category'])

        # Get answer
        result = system.answer_question(messy_query, tracker)
        answer = result['answer']

        # Check if using document (wrong) or training (correct)
        verdict = check_answer_uses_wrong_fact(
            answer,
            test['expected_wrong'],
            test['actual_correct']
        )

        results[verdict.lower()] += 1

        detailed_results.append({
            'question': test['question'],
            'messy_query': messy_query,
            'expected_wrong': test['expected_wrong'],
            'actual_correct': test['actual_correct'],
            'answer': answer,
            'verdict': verdict,
            'category': test['category']
        })

        status = "OK" if verdict == "USES_DOCUMENT" else "BAD" if verdict == "USES_TRAINING" else "??"
        print(f"[{i+1:02d}] {status} | {test['question'][:45]}...")

        if verdict == "USES_TRAINING":
            print(f"      Expected WRONG: {test['expected_wrong'][:40]}...")
            ans_clean = answer[:50].encode('ascii', 'replace').decode()
            print(f"      Got (from training): {ans_clean}...")

    # Report
    print()
    print("=" * 80)
    print("ULTIMATE RESULTS")
    print("=" * 80)
    print()

    total = len(test_sample)
    doc_pct = results['uses_document'] / total * 100
    train_pct = results['uses_training'] / total * 100
    unclear_pct = results['unclear'] / total * 100

    print(f"Uses Document (WRONG facts) - GOOD: {results['uses_document']}/{total} ({doc_pct:.1f}%)")
    print(f"Uses Training (correct facts) - BAD: {results['uses_training']}/{total} ({train_pct:.1f}%)")
    print(f"Unclear:                             {results['unclear']}/{total} ({unclear_pct:.1f}%)")
    print()
    print(f"Total Cost: {tracker.report()}")
    print()

    # Honest verdict
    print("=" * 80)
    print("HONEST VERDICT")
    print("=" * 80)
    print()

    if doc_pct >= 70:
        print(f"SYSTEM WORKS! {doc_pct:.1f}% of answers came from documents, not training.")
        print("The agentic approach with metadata + vectors genuinely retrieves from docs.")
    elif doc_pct >= 50:
        print(f"PARTIALLY WORKS. {doc_pct:.1f}% from docs, but {train_pct:.1f}% still from training.")
        print("System reads docs but Claude sometimes ignores them for known facts.")
    else:
        print(f"SYSTEM DOESN'T WORK. Only {doc_pct:.1f}% from docs.")
        print("Claude is mostly using training knowledge, not the provided documents.")

    print()
    print("SAMPLE FAILURES (where Claude ignored documents):")
    failures = [r for r in detailed_results if r['verdict'] == 'USES_TRAINING']
    for f in failures[:5]:
        print(f"  Q: {f['question'][:50]}...")
        print(f"  Doc says: {f['expected_wrong'][:40]}...")
        ans_clean = f['answer'][:40].encode('ascii', 'replace').decode()
        print(f"  Claude said: {ans_clean}...")
        print()

    return {
        'uses_document_pct': doc_pct,
        'uses_training_pct': train_pct,
        'unclear_pct': unclear_pct,
        'total_cost': tracker.get_cost(),
        'detailed_results': detailed_results
    }


if __name__ == "__main__":
    results = run_ultimate_fake_test()

    # Save results (without detailed for size)
    save_results = {k: v for k, v in results.items() if k != 'detailed_results'}
    with open("fake_facts_results.json", "w") as f:
        json.dump(save_results, f, indent=2)

    print(f"\nResults saved to fake_facts_results.json")
