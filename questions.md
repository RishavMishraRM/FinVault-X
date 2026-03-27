🧪 Test 1: Standard Vector RAG (Branch B)
This tests the default pipeline for a standard, non-relational lookup.

Question: "What are the requirements for opening a savings deposit account?"
Expected UI Result:
🧠 Cache: Not Found (Red)
🕸️ Knowledge Graph: Not reached (Gray)
📊 Vector DB: found here (Green)
🤖 Local LLM: reached (Green)

------------------------------------------------------------------------------

🧪 Test 2: Knowledge Graph (Branch A)
This tests the Semantic Router detecting a relational keyword (e.g., "difference", "compare", "between") and actively grabbing linked entities from the graph.

Question: "What is the difference between RBI and SBI?"
Expected UI Result:
🧠 Cache: Not Found (Red)
🕸️ Knowledge Graph: found here (Green)
📊 Vector DB: Not reached (Gray)
🤖 Local LLM: reached (Green)

------------------------------------------------------------------------------

🧪 Test 3: Graph Fallback to Vector DB
This tests your system's built-in safety net. We will force the router to pick the Graph by using the keyword "impact", but we will ask about something that isn't connected in the Graph, forcing the fallback.

Question: "What is the impact of late payment penalties?"
Expected UI Result:
🧠 Cache: Not Found (Red)
🕸️ Knowledge Graph: Not Found (Red) (It checked but found nothing)
📊 Vector DB: found here (Green) (Safely falls back to Vector!)
🤖 Local LLM: reached (Green)

------------------------------------------------------------------------------

🧪 Test 4: Cache Layer (CAG / Step 2)
This tests your fast-retrieval semantic caching. We will trick it by asking a question that is semantically similar (>0.85 similarity) to Test 1 to see if it bypasses the LLM entirely.

Wait a few seconds, then ask: "Tell me the required documents to open a savings account." (Or just type the exact text from Test 1 again)
Expected UI Result:
🧠 Cache: found here (Green)
🕸️ Knowledge Graph: Not reached (Gray)
📊 Vector DB: Not reached (Gray)
🤖 Local LLM: Not reached (Gray)
You will also see the "⚡ Matched Past Query" label appear at the top!

------------------------------------------------------------------------------

🧪 Test 5: Guaranteed Knowledge Graph (Branch A)
This uses keywords like "compare" or "difference" AND multiple entities to trigger the Graph router.
The Graph now returns "mentions" if facts aren't found, so it will turn Green for valid entities!

Question: "Compare RBI and SBI policies on savings account."
Expected UI Result:
🧠 Cache: Not Found (Red)
🕸️ Knowledge Graph: found here (Green)
📊 Vector DB: Not reached (Gray)
🤖 Local LLM: reached (Green)

------------------------------------------------------------------------------