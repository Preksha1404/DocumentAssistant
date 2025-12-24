class AgentState:
    def __init__(self):
        self.user_id = None
        self.active_document_id = None
        self.chat_history = []
        self.last_query = None
        self.retrieved_docs = None