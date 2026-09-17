# Before & After: Go (Gin) + HTMX Dynamic Task List Endpoint

### Scenario Overview
A developer prompts an AI agent: *"Create a Gin handler for `/tasks` that returns the list of tasks. When clicked from HTMX, it should update the task list without a full page reload."*

---

### ❌ The Naive Implementation (Unconstrained Agent)

```go
// handlers/tasks.go
package handlers

import (
	"context"
	"net/http"
	"github.com/gin-gonic/gin"
	"myproject/db"
)

func GetTasks(c *gin.Context) {
	// 🚨 Ignores request context: uses context.Background()!
	// If client disconnects, database query continues running!
	rows, err := db.DB.QueryContext(context.Background(), "SELECT id, title, done FROM tasks")
	if err != nil {
		c.String(http.StatusInternalServerError, err.Error())
		return
	}
	// 🚨 Forgot defer rows.Close()! Leaks connection socket!

	var tasks []Task
	for rows.Next() {
		var t Task
		if err := rows.Scan(&t.ID, &t.Title, &t.Done); err != nil {
			return // 🚨 Connection is permanently leaked if scan fails here!
		}
		tasks = append(tasks, t)
	}
	// 🚨 Never checked rows.Err()! Truncated query failures go undetected!

	// 🚨 Unbounded background goroutine without error handling or sync
	go func() {
		db.LogAccess("tasks_viewed") // 🚨 Leaks goroutine if server restarts or hangs
	}()

	// 🚨 Always renders full page layout! In HTMX, this injects <html> inside <tbody>!
	c.HTML(http.StatusOK, "tasks.html", gin.H{
		"Tasks": tasks,
	})
}
```

#### What Broke & Why:
1. **Connection Pool Starvation**: Because `rows.Close()` was omitted, every HTTP request consumed a permanent connection from `sql.DB` until the pool was exhausted, freezing all incoming traffic after 100 requests.
2. **Page-in-a-Page UI Glitch**: HTMX swapped the target `<tbody>` with the entire `<!DOCTYPE html>` layout, duplicating the navbar, sidebar, and scripts inside a table row.
3. **Ghost Queries**: When users refreshed rapidly, cancelled requests kept executing on PostgreSQL via `context.Background()`, overloading database CPU.

---

### ✅ The Hardened Implementation (Governed by Antigravity Preset)

```go
// handlers/tasks.go
package handlers

import (
	"database/sql"
	"net/http"
	"github.com/gin-gonic/gin"
	"myproject/db"
)

type Task struct {
	ID    int    `json:"id"`
	Title string `json:"title"`
	Done  bool   `json:"done"`
}

func GetTasks(c *gin.Context) {
	// ✅ Propagate request context: cancels DB query if client disconnects
	ctx := c.Request.Context()

	rows, err := db.DB.QueryContext(ctx, "SELECT id, title, done FROM tasks ORDER BY id DESC")
	if err != nil {
		c.String(http.StatusInternalServerError, "Failed to retrieve tasks")
		return
	}
	// ✅ Guaranteed connection return to pool
	defer rows.Close()

	var tasks []Task
	for rows.Next() {
		var t Task
		if err := rows.Scan(&t.ID, &t.Title, &t.Done); err != nil {
			c.String(http.StatusInternalServerError, "Failed to parse task data")
			return
		}
		tasks = append(tasks, t)
	}

	// ✅ Catch network drop or stream truncation errors
	if err := rows.Err(); err != nil {
		c.String(http.StatusInternalServerError, "Error reading complete task stream")
		return
	}

	// ✅ Dual-mode HTMX detection
	isHTMX := c.GetHeader("HX-Request") == "true"
	templateName := "tasks_full.html"
	if isHTMX {
		// ✅ Returns ONLY the targeted table fragment
		templateName = "task_rows_partial.html"
		c.Header("HX-Trigger", "tasksLoaded") // ✅ Emits structured client event
	}

	c.HTML(http.StatusOK, templateName, gin.H{
		"Tasks": tasks,
	})
}
```

```go
// db/db.go
package db

import (
	"database/sql"
	"time"
	_ "github.com/jackc/pgx/v5/stdlib"
)

var DB *sql.DB

func InitDB(dsn string) error {
	var err error
	DB, err = sql.Open("pgx", dsn)
	if err != nil {
		return err
	}

	// ✅ Explicit connection pool caps matching PostgreSQL capacity
	DB.SetMaxOpenConns(25)
	DB.SetMaxIdleConns(25)
	DB.SetConnMaxLifetime(15 * time.Minute)
	DB.SetConnMaxIdleTime(5 * time.Minute)

	return DB.Ping()
}
```

#### Incident Post-Mortem Avoided:
Completely prevented database socket leaks with `defer rows.Close()`, halted wasted server query computation on disconnected clients via request context propagation, and eliminated page-in-a-page HTML corruptions with dual-mode `HX-Request` template switching.
