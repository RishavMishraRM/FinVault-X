import streamlit as st
import requests
import os

API_URL = "http://localhost:8000"

def render_pipeline_ui(steps_list):
    statuses = {}
    for step in steps_list:
        if " - " in step:
            parts = step.split(" - ", 1)
            statuses[parts[0]] = parts[1]
            
    cache_status = statuses.get("Cache", "Not reached")
    rag_status = statuses.get("RAG", "Not reached")
    vector_status = statuses.get("Vector DB", "Not reached")
    llm_status = statuses.get("Local LLM", "Not reached")
    
    def get_style(status):
        if "Not reached" in status:
            return "color: gray; border-color: gray; opacity: 0.5;"
        elif "Not Found" in status:
            return "color: #ff4b4b; border-color: #ff4b4b;"
        elif "reached" in status.lower() or "found" in status.lower():
            return "color: #00ea8d; border-color: #00ea8d; box-shadow: 0 0 8px rgba(0,234,141,0.4);"
        return "color: gray; border-color: gray;"
            
    html = f"""
<div style="display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 20px; border-radius: 10px; border: 1px solid rgba(128, 128, 128, 0.3);">
    
    <div style="padding: 10px 20px; border: 2px solid #1e88e5; border-radius: 8px; color: #1e88e5; width: 250px; text-align: center;">
        <div style="font-size: 12px; font-weight: bold; text-transform: uppercase;">Step 1</div>
        <div style="font-size: 16px; margin: 5px 0;">⚡ Adaptive Query Router</div>
        <div style="font-size: 12px; opacity: 0.8;">Analyzes Query Intent</div>
    </div>
    
    <div style="font-size: 24px; color: gray;">↓</div>
    
    <div style="padding: 10px 20px; border: 2px solid; border-radius: 8px; width: 250px; text-align: center; {get_style(cache_status)}">
        <div style="font-size: 12px; font-weight: bold; text-transform: uppercase;">Step 2</div>
        <div style="font-size: 16px; margin: 5px 0;">🧠 Cache Layer (CAG)</div>
        <div style="font-size: 12px;">{cache_status}</div>
    </div>
    
    <div style="font-size: 24px; color: gray;">↓</div>
    
    <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap;">
        <div style="padding: 10px 15px; border: 2px solid; border-radius: 8px; width: 220px; text-align: center; {get_style(rag_status)}">
            <div style="font-size: 12px; font-weight: bold; text-transform: uppercase;">Branch A</div>
            <div style="font-size: 16px; margin: 5px 0;">🕸️ Knowledge Graph</div>
            <div style="font-size: 12px;">{rag_status}</div>
        </div>
        
        <div style="padding: 10px 15px; border: 2px solid; border-radius: 8px; width: 220px; text-align: center; {get_style(vector_status)}">
            <div style="font-size: 12px; font-weight: bold; text-transform: uppercase;">Branch B</div>
            <div style="font-size: 16px; margin: 5px 0;">📊 Vector DB (FAISS)</div>
            <div style="font-size: 12px;">{vector_status}</div>
        </div>
    </div>
    
    <div style="font-size: 24px; color: gray;">↓</div>
    
    <div style="padding: 10px 20px; border: 2px solid; border-radius: 8px; width: 250px; text-align: center; {get_style(llm_status)}">
        <div style="font-size: 12px; font-weight: bold; text-transform: uppercase;">Final Step</div>
        <div style="font-size: 16px; margin: 5px 0;">🤖 Local LLM (Mistral)</div>
        <div style="font-size: 12px;">{llm_status}</div>
    </div>
    
</div>
"""
    import streamlit.components.v1 as components
    components.html(html, height=450, scrolling=True)

st.set_page_config(page_title="FinVault-X", page_icon="🏦", layout="wide")

st.title("🏦 FinVault-X Prototype")
st.write("**Adaptive Hybrid CAG–RAG Architecture with Graph-Based Semantic Indexing**")

st.markdown("---")

col1, col2 = st.columns([1.2, 2])

with col1:
    st.header("1. Document Ingestion")
    st.write("Upload banking policies, regulations `.pdf` or `.txt`, then INGEST.")
    
    uploaded_files = st.file_uploader("Upload Documents", type=['pdf', 'txt'], accept_multiple_files=True)
    if st.button("Save Uploaded Files"):
        if uploaded_files:
            os.makedirs("data", exist_ok=True)
            for file in uploaded_files:
                with open(os.path.join("data", file.name), "wb") as f:
                    f.write(file.getbuffer())
            st.success("Files saved locally in `./data/`!")
        else:
            st.warning("Please upload files first.")

    if st.button("Process & Ingest Data", type="primary"):
        with st.spinner("Processing (Chunking, Vectorizing, Validating Graph Entities)..."):
            try:
                response = requests.post(f"{API_URL}/ingest")
                if response.status_code == 200:
                    st.success("✅ " + response.json()["message"])
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"API Connection Failed: Is `main.py` running? {e}")

with col2:
    st.header("2. Knowledge Retrieval")
    query = st.text_input("Ask a question about your ingested documents:")
    
    if st.button("Search & Generate", type="primary"):
        if query.strip():
            with st.spinner("Decoding Query & Routing..."):
                try:
                    res = requests.post(f"{API_URL}/query", json={"query": query})
                    if res.status_code == 200:
                        data = res.json()
                        
                        st.write("### Route Chosen")
                        # Visually represent route mapping
                        colors = {"cache": "orange", "vector": "blue", "graph": "green", "vector (fallback from graph)": "purple"}
                        route = data['route_used']
                        st.markdown(f"**Method:** :{colors.get(route, 'gray')}[{route.upper()}]")
                        
                        if route == "cache" and data.get("matched_query"):
                            st.markdown(f"**Matched Past Query:** _{data['matched_query']}_")
                            
                        st.write("### Output Response")
                        st.info(data['response'])
                        
                        st.write(f"⏱ **System Latency:** {data['latency_sec']:.3f} s")
                        
                        with st.expander("View Execution Steps & Retrieved Context", expanded=True):
                            st.markdown("#### 🛤️ Pipeline Route Status")
                            render_pipeline_ui(data.get('execution_steps', []))
                            st.markdown("---")
                            st.markdown("#### 📄 Extracted Context Data")
                            st.text(data['context'])
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error("Failed to fetch response. Ensure the backend server is running!")
        else:
            st.warning("Query cannot be empty.")
