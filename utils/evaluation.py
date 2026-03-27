import time

class EvaluationMetrics:
    def __init__(self):
        self.queries_processed = 0
        self.total_latency = 0.0
        self.start_time = 0.0
        
    def start_timer(self):
        self.start_time = time.time()
        
    def end_timer(self):
        latency = time.time() - self.start_time
        self.total_latency += latency
        self.queries_processed += 1
        return latency
        
    def get_average_latency(self) -> float:
        if self.queries_processed == 0:
            return 0.0
        return self.total_latency / self.queries_processed

    def calculate_retrieval_accuracy(self, retrieved_context: str, true_context: str) -> float:
        """Simple token overlap accuracy for evaluation demonstration"""
        if not true_context:
            return 1.0
        if not retrieved_context:
            return 0.0
            
        ret_words = set(retrieved_context.lower().split())
        true_words = set(true_context.lower().split())
        
        if len(true_words) == 0:
            return 1.0
            
        overlap = len(ret_words.intersection(true_words))
        return overlap / len(true_words)
