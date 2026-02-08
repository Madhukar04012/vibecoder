# VibeCoder Login Quick Start Guide

## ✅ Status: Backend is WORKING!

The authentication system is fully functional. If you're having login issues, follow the troubleshooting steps below.

---

## 🚀 Quick Start

### 1. **Start the Backend** (if not already running)
```powershell
# From project root
C:/Users/annam/vibecober/.venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 2. **Start the Frontend** (if not already running)
```powershell
# From project root
cd frontend
npm run dev
```

### 3. **Test Login**
- Open: http://localhost:5173/login
- **Default Test Account:**
  - Email: `admin@test.com`
  - Password: `admin123`

- **Your Existing Accounts:**
  - annammadhukarreddy53@gmail.com
  - annammadhukarreddy54@gmail.com

---

## 🔧 Troubleshooting

### If Login Fails in Browser:

#### 1. **Clear Browser Storage**
Open browser console (F12) and run:
```javascript
localStorage.clear();
location.reload();
```

#### 2. **Check Browser Console for Errors**
- Open DevTools (F12)
- Go to Console tab
- Look for any red error messages
- Common issues:
  - "Failed to fetch" → Backend not running
  - "CORS error" → Check backend CORS settings
  - "401 Unauthorized" → Wrong credentials

#### 3. **Verify Backend is Running**
Visit: http://localhost:8000/api/status

You should see:
```json
{"status":"VibeCober API running","version":"0.6.1"}
```

#### 4. **Test Login via API**
Run the test script:
```powershell
C:/Users/annam/vibecober/.venv/Scripts/python.exe test_frontend_login.py
```

#### 5. **Check Database**
```powershell
C:/Users/annam/vibecober/.venv/Scripts/python.exe check_db.py
```

---

## 📝 Available Test Users

| Email | Password | Notes |
|-------|----------|-------|
| admin@test.com | admin123 | Default test account |
| test@example.com | testpass123 | Created during testing |
| frontendtest@example.com | Test123! | Created during testing |
| annammadhukarreddy53@gmail.com | (your password) | Your account |
| annammadhukarreddy54@gmail.com | (your password) | Your account |

---

## 🛠️ Easy Startup Scripts

### Windows Batch Files (Already in root):
- `start-backend.bat` - Starts backend server
- `start-frontend.bat` - Starts frontend server
- `start.bat` - Starts both servers

---

## 🐛 Common Issues & Solutions

### Issue: "Cannot connect to server"
**Solution:** Backend not running on port 8000
```powershell
C:/Users/annam/vibecober/.venv/Scripts/python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Issue: "Invalid email or password"
**Solutions:**
1. Use the default test account: `admin@test.com` / `admin123`
2. Check if you registered with this email
3. Reset password (if implemented) or create new account

### Issue: "Port 8000 already in use"
**Solution:** Kill existing process
```powershell
# Find process on port 8000
netstat -ano | Select-String ":8000" | Select-String "LISTENING"
# Kill it (replace PID with actual process ID)
Stop-Process -Id <PID> -Force
```

### Issue: Login works but redirects immediately
**Solution:** Token storage issue
```javascript
// In browser console
localStorage.setItem('vibecober_token', 'test');
console.log(localStorage.getItem('vibecober_token'));
localStorage.clear();
```

---

## ✅ Verification Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Database has users (check with `check_db.py`)
- [ ] API status endpoint responds: http://localhost:8000/api/status
- [ ] Browser localStorage is clear
- [ ] Using correct credentials

---

## 📞 Need Help?

1. Check the test scripts output:
   - `test_frontend_login.py` - Tests API directly
   - `check_db.py` - Shows database users

2. Check browser Network tab (F12 → Network) to see actual requests

3. Look at backend terminal for request logs - you should see:
   ```
   INFO: 127.0.0.1:xxxxx - "POST /auth/login HTTP/1.1" 200 OK
   ```

---

## 🎯 Login is WORKING!

The backend authentication is fully functional and tested. If you still have issues, it's likely:
1. Browser cache/localStorage
2. Wrong credentials
3. Frontend not connecting to backend properly

**Try the default account first: admin@test.com / admin123**
