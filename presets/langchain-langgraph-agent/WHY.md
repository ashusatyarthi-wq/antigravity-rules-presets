# Why These LangGraph Rules Exist

### 1. Why require `extra="forbid"` on Pydantic tool schemas?
When language models execute tool calling on complex agent workflows, models like Claude, GPT-4, and Gemini frequently invent plausible-sounding parameters that do not exist in the python signature (e.g. adding `format="json"` or `verbose=True` to a search tool). Under default Pydantic, unknown parameters are silently ignored or cause confusing downstream validation errors. `extra="forbid"` immediately flags invalid schemas at the tool interface boundary.

### 2. Why require explicit `recursion_limit`?
Autonomous agent graphs containing conditional cycles (`model -> should_continue -> tools -> model`) will enter infinite execution loops if the model fails to satisfy its stopping criteria or if a tool keeps returning repeated errors. Without a hard recursion cap, a single stuck agent can burn $50–$200 in API tokens in minutes.

### 3. Why message-trimming before model invocation?
Long-running agent threads accumulate thousands of tokens of intermediate tool call JSON and error tracebacks. Without active windowing, the agent hits the model's context ceiling, resulting in either truncated responses or exponential cost spikes per turn.
