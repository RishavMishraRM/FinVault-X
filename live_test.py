
import requests
import time

API_BASE = "http://localhost:8000"

def run_functional_test():
    print("--- STARTING LIVE BACKEND FUNCTIONAL TEST ---")
    
    # 1. Ingest
    print("\n[Step 1] Triggering Ingestion...")
    try:
        res = requests.post(f"{API_BASE}/ingest", timeout=300)
        print(f"Ingest Result: {res.status_code} - {res.json()['message']}")
    except Exception as e:
        print(f"Ingest FAILED: {e}")
        return

    # 2. Test Knowledge Graph Query
    query = "Compare RBI and SBI policies on savings account."
    print(f"\n[Step 2] Testing Query: '{query}'")
    try:
        res = requests.post(f"{API_BASE}/query", json={"query": query}, timeout=300)
        data = res.json()
        print(f"Query Status: {res.status_code}")
        print(f"Route Used: {data['route_used']}")
        print(f"Execution Steps:")
        for step in data['execution_steps']:
            print(f"  - {step}")
            
        # Check if RAG is 'found here'
        rag_step = next(s for s in data['execution_steps'] if s.startswith("RAG"))
        if "found here" in rag_step:
            print("\n✅ SUCCESS: Knowledge Graph branch triggered and found results!")
        else:
            print("\n❌ FAILURE: Knowledge Graph branch returned 'Not Found'.")
            
    except Exception as e:
        print(f"Query FAILED: {e}")

if __name__ == "__main__":
    time.sleep(5) # Wait for server
    run_functional_test()
