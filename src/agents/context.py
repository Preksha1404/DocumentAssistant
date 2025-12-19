class AgentContext:
    def __init__(self):
        self.user_id: int | None = None
        self.active_document_id: int | None = None
        self.retrieved_docs: str | None = None
        self.last_query: str | None = None

context = AgentContext()