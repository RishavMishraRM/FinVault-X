import networkx as nx
import spacy
from typing import List, Dict

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            import os
            # If not installed, handle elegantly without crashing hard
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def build_from_documents(self, documents: List[Dict]):
        for doc in documents:
            text = doc["content"]
            metadata = doc["metadata"]
            
            # Simple Entity Extraction via spaCy
            doc_nlp = self.nlp(text)
            
            allowed_labels = ["ORG", "LAW", "MONEY", "PRODUCT", "GPE", "NORP"]
            entities = [ent.text.lower() for ent in doc_nlp.ents if ent.label_ in allowed_labels]
            
            if not entities:
                continue
                
            doc_node_id = f"PAGE_{metadata.get('page', 1)}_{metadata.get('source', '')[-15:]}"
            self.graph.add_node(doc_node_id, type="document", metadata=metadata)
            
            # Link Document to Entities
            for ent in entities:
                self.graph.add_node(ent, type="entity")
                self.graph.add_edge(doc_node_id, ent, relation="mentions")
                
            # Naive Relation Extraction between Entities inside the same sentence
            for sent in doc_nlp.sents:
                sent_ents = [ent.text.lower() for ent in sent.ents if ent.label_ in allowed_labels]
                
                # Check for explicit keywords linking entities
                relation_label = "co_occurs_with"
                sent_lower = sent.text.lower()
                if "affects" in sent_lower or "impacts" in sent_lower:
                    relation_label = "affects / impacts"
                elif "depends on" in sent_lower:
                    relation_label = "depends_on"
                elif "regulated by" in sent_lower:
                    relation_label = "regulated_by"
                
                for i in range(len(sent_ents)):
                    for j in range(i+1, len(sent_ents)):
                        if sent_ents[i] != sent_ents[j]:
                            # Add bi-directional link for co-occurrence
                            self.graph.add_edge(sent_ents[i], sent_ents[j], relation=relation_label)
                            self.graph.add_edge(sent_ents[j], sent_ents[i], relation=relation_label)

    def search(self, query: str, depth: int = 1) -> str:
        if len(self.graph.nodes) == 0:
            return ""
            
        query_nlp = self.nlp(query)
        # 1. Try search using Entities and Noun Chunks
        query_terms = [ent.text.lower().strip() for ent in query_nlp.ents]
        query_terms += [chunk.text.lower().strip() for chunk in query_nlp.noun_chunks]
        
        # 2. Extract keywords manually if no entities/chunks found
        if not query_terms:
            query_terms = [t.lower().strip() for t in query.split() if len(t) > 3]

        context_facts = []
        
        # Filter terms to find matching nodes (including partial matches)
        matching_nodes = []
        for term in set(query_terms):
            # Exact match
            if term in self.graph.nodes:
                matching_nodes.append(term)
            else:
                # Partial match (is term inside a node name or vice versa?)
                for node in self.graph.nodes:
                    if term in node or node in term:
                        matching_nodes.append(node)
        
        for node in set(matching_nodes):
            try:
                # MUST use undirected=True to find documents pointing TO the entity
                subgraph = nx.ego_graph(self.graph, node, radius=depth, undirected=True)
                for u, v, data in subgraph.edges(data=True):
                    rel = data.get('relation')
                    if rel == "mentions":
                        context_facts.append(f"Graph Fact: Document {u} contains reference to '{v}'")
                    else:
                        context_facts.append(f"Graph Fact: '{u}' {rel} '{v}'")
            except:
                continue
                    
        # Return unique facts
        unique_facts = list(set(context_facts))
        if not unique_facts:
            return ""
            
        return "\n".join(unique_facts[:15]) # Return top 15 facts
