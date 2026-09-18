# Antigravity Preset: LangGraph & LangChain Python Agentic Systems

This configuration hardens Google Antigravity agents operating on LangGraph state machines, multi-agent swarms, and Python-based tool-calling workflows.

---

## 1. Graph Execution & Recursion Circuit Breakers
- **Recursion Limit Hardening**:
  - Never invoke a LangGraph compiled graph without an explicit `recursion_limit` config:
    ```python
    config = {"recursion_limit": 25, "configurable": {"thread_id": thread_id}}
    ```
  - Treat hitting `GraphRecursionError` as a hard failure requiring graph pruning, never catch-and-retry blindly.
- **State Reducer Safety**:
  - When annotating state with `Annotated[list, add_messages]`, always verify message deduplication by `id`.
  - Never replace the full message history unless performing an explicit graph compaction or rolling-window purge.

---

## 2. Tool Calling & Validation Contracts
- **Pydantic v2 Strict Mode**:
  - All tools must define input arguments via Pydantic v2 models with `model_config = ConfigDict(extra="forbid", strict=True)`.
  - Provide human-readable field descriptions: LLM parameter hallucination correlates directly with missing docstrings.
- **Circuit Breaker on Tool Exceptions**:
  - Wrap external network tools in `try..except` returning structured `ToolMessage(content=f"Error: {e}", status="error")` instead of letting uncaught exceptions crash the graph runner.
  - Apply exponential backoff with full jitter on upstream model rate limits (`429 Too Many Requests`).

---

## 3. Context & Token Window Protection
- **Automatic History Compaction**:
  - Graphs maintaining multi-turn conversations must integrate `trim_messages` or `filter_messages` before routing to model nodes.
  - Bound system prompt + scratchpad size to <= 60% of the target context window to reserve token budget for structured generation.

---

## 4. Verification Protocol
1. Run graph visualization check: `graph.get_graph().draw_ascii()` or export Mermaid syntax to verify all conditional edges terminate at `END`.
2. Execute state unit tests:
   ```bash
   pytest tests/test_agent_state.py -v --timeout=30
   ```
3. Test tool failure tolerance by mocking a 500 error on the primary tool and asserting the graph recovers or exits cleanly.
