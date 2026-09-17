# Before & After: FastAPI + Async SQLAlchemy 2.0 User Orders Endpoint

### Scenario Overview
A developer prompts an AI agent: *"Create an API endpoint `/users/{id}` that returns the user and their list of recent orders."*

---

### ❌ The Naive Implementation (Unconstrained Agent)

```python
# routes/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import User
from database import sync_session_factory # 🚨 Blocking sync session in async FastAPI!

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    # 🚨 Synchronous blocking call inside async event loop!
    session: Session = sync_session_factory()
    
    # 🚨 No eager loading configured
    user = session.query(User).filter(User.id == user_id).first()
    
    # 🚨 Returns raw ORM object: triggers lazy-load or leaks password hash!
    # In async SQLAlchemy, this immediately throws MissingGreenlet exception!
    return user 
```

#### What Broke & Why:
1. **Event Loop Starvation**: Calling synchronous `session.query()` inside an `async def` route blocks Python's single-threaded `asyncio` event loop for all concurrent users while waiting on network database I/O.
2. **Crash on Serialization (`MissingGreenlet`)**: When FastAPI attempts to serialize `user.orders` to JSON, SQLAlchemy tries to lazy-load the orders, throwing a fatal `MissingGreenlet` error and returning HTTP 500.
3. **Sensitive Field Leakage**: Returning the raw `User` model serializes internal columns (such as `hashed_password` and `security_stamp`) directly into public API responses.

---

### ✅ The Hardened Implementation (Governed by Antigravity Preset)

```python
# schemas/user.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List

class OrderItemResponse(BaseModel):
    id: int
    total_amount: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserDetailResponse(BaseModel):
    id: int
    email: str
    full_name: str
    orders: List[OrderItemResponse] = []
    # ✅ Only explicitly whitelisted fields are exposed
    # hashed_password is completely omitted!
    model_config = ConfigDict(from_attributes=True)
```

```python
# routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from models import User
from schemas.user import UserDetailResponse

router = APIRouter(tags=["Users"])

@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db) # ✅ Managed async session dependency
):
    # ✅ Explicit async select with eager relationship pre-fetching
    query = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.orders)) # ✅ Eliminates MissingGreenlet
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} does not exist."
        )

    # ✅ Safe, typed serialization via Pydantic v2 DTO
    return user
```

```python
# database.py
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost:5432/app_db",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True, # ✅ Auto-reconnect on dropped sockets
    pool_recycle=1800,
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback() # ✅ Guaranteed rollback prevents leaked locks
            raise
```

#### Incident Post-Mortem Avoided:
Prevented event loop blocking, completely eliminated `MissingGreenlet` serialization crashes via explicit `selectinload()`, and protected sensitive credentials from leaking to public API clients.
