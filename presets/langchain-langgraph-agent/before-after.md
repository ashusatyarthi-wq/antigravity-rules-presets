# Before vs After: LangGraph Agent Rules

## Scenario: Tool Throws Transient API Error

### Before (Standard Default Agent Setup)
```python
@tool
def fetch_user_data(user_id: str):
    # Network call throws 503 Service Unavailable
    response = requests.get(f"https://api.internal/users/{user_id}")
    return response.json()

# Uncaught exception crashes the entire LangGraph runner.
# Agent state is lost. User gets a 500 Internal Server Error.
```

### After (Antigravity Hardened Rules)
```python
class FetchUserInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    user_id: str = Field(description="Alphanumeric UUID of the target user")

@tool(args_schema=FetchUserInput)
def fetch_user_data(user_id: str) -> str:
    try:
        response = http_client.get(f"https://api.internal/users/{user_id}", timeout=10)
        return response.text
    except Exception as e:
        # Returns structured ToolMessage status
        return f"TOOL_ERROR: Upstream user service unavailable ({str(e)}). Please retry or ask user for confirmation."

# Graph catches error cleanly, routes to fallback node, and explains delay to user without crashing.
```
