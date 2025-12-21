"""
ULTIMATE LEGAL DOCUMENTS TEST - Agent Does EVERYTHING
======================================================

Real world scenario:
- 100 messy legal PDFs (various formats)
- Agent extracts text from PDFs (no manual extraction)
- Agent creates metadata
- Agent builds vector index
- Agent answers complex legal questions
- Messy Indianized queries

Model: Haiku ONLY
Documents: ~100 real legal PDFs
NO CHEATING - Agent handles everything
"""

import anthropic
import numpy as np
import json
import os
import random
from pathlib import Path
from dotenv import load_dotenv

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


def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF - Agent does this, no manual intervention.
    Uses PyPDF2 or pdfplumber - common real-world scenario.
    """
    text = ""

    # Try PyPDF2 first
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[:10]:  # First 10 pages max
                text += page.extract_text() or ""
        if len(text.strip()) > 100:
            return text[:15000]  # Limit to 15k chars
    except:
        pass

    # Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:10]:
                text += page.extract_text() or ""
        if len(text.strip()) > 100:
            return text[:15000]
    except:
        pass

    # Try pymupdf (fitz)
    try:
        import fitz
        doc = fitz.open(pdf_path)
        for page in doc[:10]:
            text += page.get_text()
        doc.close()
        if len(text.strip()) > 100:
            return text[:15000]
    except:
        pass

    return text[:15000] if text else None


def extract_text_from_html(html_path):
    """Extract text from HTML file"""
    try:
        from bs4 import BeautifulSoup
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            return text[:15000]
    except:
        return None


def load_all_legal_documents(folder_path):
    """
    Load all documents from folder - Agent handles extraction.
    Supports PDF, HTML, TXT - real world messy scenario.
    """
    documents = {}
    folder = Path(folder_path)

    print(f"Loading documents from {folder}...")

    files = list(folder.glob('*'))
    success = 0
    failed = 0

    for filepath in files:
        doc_id = filepath.stem
        text = None

        if filepath.suffix.lower() == '.pdf':
            text = extract_text_from_pdf(filepath)
        elif filepath.suffix.lower() in ['.html', '.htm']:
            text = extract_text_from_html(filepath)
        elif filepath.suffix.lower() == '.txt':
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()[:15000]
            except:
                pass

        if text and len(text.strip()) > 200:
            documents[doc_id] = {
                'content': text,
                'filepath': str(filepath),
                'size': len(text)
            }
            success += 1
        else:
            failed += 1

    print(f"  Successfully loaded: {success}")
    print(f"  Failed to extract: {failed}")

    return documents


def agent_create_metadata(doc_id, doc_content, tracker):
    """
    Agent creates metadata from document using Haiku.
    This is the core of the agentic approach.
    """
    # Truncate content for prompt
    content_preview = doc_content[:3000]

    prompt = f"""Analyze this legal document and create comprehensive search metadata.

DOCUMENT: {doc_id}
---
{content_preview}
---

Create metadata with:
1. Main legal topics and concepts
2. Key sections, acts, or laws mentioned
3. Important legal terms and definitions
4. Common questions someone might ask about this
5. Informal/Hinglish variations (e.g., "kya hai", "kaise kare")

Output a single dense paragraph with all terms separated by |
Be comprehensive - include numbers, sections, legal jargon."""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=400,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    tracker.add(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text.strip()


def agent_create_qa_pairs(doc_id, doc_content, tracker):
    """
    Agent creates Q&A pairs from document for testing.
    """
    content_preview = doc_content[:4000]

    prompt = f"""From this legal document, create 5 specific factual questions with answers.

DOCUMENT: {doc_id}
---
{content_preview}
---

Create 5 Q&A pairs:
- Questions should require specific facts from the document
- Include section numbers, penalties, time limits, definitions
- Mix formal and informal question styles
- Some in Hinglish (Hindi+English)

Format:
Q1: [specific question]
A1: [short factual answer with exact details]
...

Focus on testable facts, not general concepts."""

    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=600,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    tracker.add(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text.strip()


def parse_qa_pairs(qa_text):
    """Parse Q&A text into structured pairs"""
    pairs = []
    lines = qa_text.split('\n')

    current_q = None
    current_a = None

    for line in lines:
        line = line.strip()
        if line.startswith('Q') and ':' in line:
            if current_q and current_a:
                pairs.append({'question': current_q, 'answer': current_a})
            current_q = line.split(':', 1)[1].strip()
            current_a = None
        elif line.startswith('A') and ':' in line:
            current_a = line.split(':', 1)[1].strip()

    if current_q and current_a:
        pairs.append({'question': current_q, 'answer': current_a})

    return pairs


class LegalAgenticSystem:
    """
    Complete agentic system for legal documents.
    Agent handles everything - extraction, metadata, search, answering.
    """

    def __init__(self, documents, tracker):
        self.tracker = tracker
        self.documents = documents
        self.metadata = {}
        self.embeddings = {}

        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        print(f"\nAgent creating metadata for {len(documents)} documents...")

        # Agent creates metadata for each document
        for i, (doc_id, doc_data) in enumerate(documents.items()):
            if i % 20 == 0:
                print(f"  Processing {i+1}/{len(documents)}...")
            self.metadata[doc_id] = agent_create_metadata(
                doc_id, doc_data['content'], tracker
            )

        print(f"\nCreating vector embeddings...")
        for doc_id, meta in self.metadata.items():
            # Combine metadata + content for embedding
            combined = f"{meta}\n\n{documents[doc_id]['content'][:2000]}"
            self.embeddings[doc_id] = self.embedder.encode(combined)

        print(f"System ready with {len(self.embeddings)} documents")

    def search(self, query, top_k=5):
        """Vector search for relevant documents"""
        query_emb = self.embedder.encode(query)

        scores = []
        for doc_id, doc_emb in self.embeddings.items():
            score = float(np.dot(query_emb, doc_emb) /
                         (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb)))
            scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def answer_question(self, query, tracker):
        """Agent answers question using retrieved documents"""
        results = self.search(query, top_k=3)

        context = ""
        for doc_id, score in results:
            context += f"\n\n=== {doc_id} (score: {score:.3f}) ===\n"
            context += self.documents[doc_id]['content'][:3000]

        prompt = f"""You are a legal assistant. Answer this question using ONLY the documents provided.

QUESTION: {query}

DOCUMENTS:
{context}

Rules:
1. Answer using ONLY facts from the documents
2. Include specific sections, numbers, penalties if mentioned
3. Be concise - 1-3 sentences
4. If information not in documents, say "Not found in documents"

Answer:"""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        tracker.add(response.usage.input_tokens, response.usage.output_tokens)

        return {
            'answer': response.content[0].text.strip(),
            'retrieved_docs': [r[0] for r in results],
            'scores': [r[1] for r in results]
        }


def create_messy_legal_query(question):
    """Convert legal question to messy Indianized format"""
    variations = [
        lambda q: f"bhai {q.lower().replace('?', '')} btao",
        lambda q: f"yaar ye {q.lower().replace('what is', 'kya hai').replace('?', '')}",
        lambda q: q.upper() + "???",
        lambda q: f"urgent {q.lower().replace('?', '')} plzz help",
        lambda q: f"koi btao {q.lower().replace('?', '')}",
        lambda q: q.replace(' ', '  ').replace('a', 'e')[:60] + "?",
        lambda q: f"haan wo {q.lower().replace('?', '')} wala",
        lambda q: f"TELL ME {q.upper().replace('?', '')}!!!",
    ]
    return random.choice(variations)(question)


def run_legal_ultimate_test():
    """Run the ultimate legal documents test"""

    print("=" * 80)
    print("ULTIMATE LEGAL DOCUMENTS TEST")
    print("Agent Does EVERYTHING - No Cheating")
    print("=" * 80)
    print()

    tracker = CostTracker()

    # Step 1: Load all documents (Agent extracts text)
    print("STEP 1: Agent Loading & Extracting Documents")
    print("-" * 50)

    documents = load_all_legal_documents('legal_docs')

    if len(documents) < 10:
        print("ERROR: Not enough documents loaded. Check PDF extraction.")
        return None

    print(f"\nLoaded {len(documents)} legal documents")
    print(f"Sample docs: {list(documents.keys())[:5]}")
    print()

    # Step 2: Build agentic system
    print("STEP 2: Agent Building System (Metadata + Vectors)")
    print("-" * 50)

    system = LegalAgenticSystem(documents, tracker)

    print(f"\nMetadata creation cost: {tracker.report()}")
    print()

    # Step 3: Agent creates test Q&A pairs
    print("STEP 3: Agent Creating Test Q&A Pairs")
    print("-" * 50)

    all_qa_pairs = []
    sample_docs = list(documents.keys())[:20]  # Use first 20 docs for testing

    for doc_id in sample_docs:
        qa_text = agent_create_qa_pairs(doc_id, documents[doc_id]['content'], tracker)
        pairs = parse_qa_pairs(qa_text)
        for pair in pairs:
            pair['source_doc'] = doc_id
            all_qa_pairs.append(pair)

    print(f"Created {len(all_qa_pairs)} Q&A pairs from {len(sample_docs)} documents")
    print(f"Sample Q&A:")
    if all_qa_pairs:
        print(f"  Q: {all_qa_pairs[0]['question'][:60]}...")
        print(f"  A: {all_qa_pairs[0]['answer'][:60]}...")
    print()

    # Step 4: Test with messy queries
    print("STEP 4: Testing with MESSY Indianized Queries")
    print("-" * 50)
    print()

    # Test on subset
    test_pairs = all_qa_pairs[:50] if len(all_qa_pairs) >= 50 else all_qa_pairs

    results = {
        'correct': 0,
        'partial': 0,
        'wrong': 0,
        'retrieval_correct': 0,
    }

    detailed = []

    for i, qa in enumerate(test_pairs):
        # Make query messy
        messy_query = create_messy_legal_query(qa['question'])

        # Get answer
        result = system.answer_question(messy_query, tracker)
        answer = result['answer'].lower()
        expected = qa['answer'].lower()

        # Check retrieval
        retrieval_ok = qa['source_doc'] in result['retrieved_docs']
        if retrieval_ok:
            results['retrieval_correct'] += 1

        # Check answer quality
        expected_keywords = set(expected.split()) - {'the', 'a', 'an', 'is', 'are', 'of', 'to', 'in', 'for'}
        answer_keywords = set(answer.split())

        overlap = len(expected_keywords & answer_keywords)
        overlap_pct = overlap / len(expected_keywords) if expected_keywords else 0

        if overlap_pct >= 0.5 or any(kw in answer for kw in list(expected_keywords)[:3]):
            results['correct'] += 1
            status = "OK"
        elif overlap_pct >= 0.2:
            results['partial'] += 1
            status = "PARTIAL"
        else:
            results['wrong'] += 1
            status = "WRONG"

        detailed.append({
            'question': qa['question'],
            'messy': messy_query,
            'expected': qa['answer'],
            'got': result['answer'],
            'status': status,
            'retrieval_ok': retrieval_ok
        })

        print(f"[{i+1:02d}] {status:7} | {qa['question'][:45]}...")

        if status == "WRONG":
            print(f"        Expected: {qa['answer'][:50]}...")
            ans_clean = result['answer'][:50].encode('ascii', 'replace').decode()
            print(f"        Got: {ans_clean}...")

    # Results
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    total = len(test_pairs)

    print(f"Documents Loaded:     {len(documents)}")
    print(f"Q&A Pairs Generated:  {len(all_qa_pairs)}")
    print(f"Queries Tested:       {total}")
    print()
    print(f"Retrieval Accuracy:   {results['retrieval_correct']}/{total} ({results['retrieval_correct']/total*100:.1f}%)")
    print(f"Correct Answers:      {results['correct']}/{total} ({results['correct']/total*100:.1f}%)")
    print(f"Partial Answers:      {results['partial']}/{total} ({results['partial']/total*100:.1f}%)")
    print(f"Wrong Answers:        {results['wrong']}/{total} ({results['wrong']/total*100:.1f}%)")
    print()
    print(f"Total Cost: {tracker.report()}")

    # Verdict
    print()
    print("=" * 80)
    print("HONEST VERDICT")
    print("=" * 80)
    print()

    accuracy = (results['correct'] + results['partial'] * 0.5) / total * 100

    if accuracy >= 70:
        print(f"EXCELLENT: {accuracy:.1f}% accuracy on complex legal documents!")
        print("Agent-based metadata + vectors works on real messy legal PDFs.")
    elif accuracy >= 50:
        print(f"ACCEPTABLE: {accuracy:.1f}% accuracy.")
        print("System works but struggles with complex legal language.")
    else:
        print(f"NEEDS WORK: {accuracy:.1f}% accuracy.")
        print("Legal domain is too complex for current approach.")

    print()
    print("SAMPLE FAILURES:")
    failures = [d for d in detailed if d['status'] == 'WRONG'][:5]
    for f in failures:
        print(f"  Q: {f['question'][:55]}...")
        print(f"  Expected: {f['expected'][:45]}...")
        ans_clean = f['got'][:45].encode('ascii', 'replace').decode()
        print(f"  Got: {ans_clean}...")
        print()

    return {
        'documents_loaded': len(documents),
        'qa_pairs': len(all_qa_pairs),
        'retrieval_accuracy': results['retrieval_correct']/total*100,
        'answer_accuracy': results['correct']/total*100,
        'partial_accuracy': results['partial']/total*100,
        'combined_accuracy': accuracy,
        'cost': tracker.get_cost()
    }


if __name__ == "__main__":
    # Install required packages if needed
    import subprocess
    import sys

    packages = ['PyPDF2', 'pdfplumber', 'beautifulsoup4']
    for pkg in packages:
        try:
            __import__(pkg.replace('-', '_').lower().split('4')[0])
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])

    results = run_legal_ultimate_test()

    if results:
        with open("legal_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to legal_test_results.json")
