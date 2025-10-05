import random
import string
from collections import defaultdict, deque
from time import time
import os

def random_name(length=10):
    first = random.choice(string.ascii_letters + '_')
    rest = ''.join(random.choices(string.ascii_letters + string.digits + '_', k=length-1))
    return first + rest

def safe_read_file(path, chunk_size=32768):
    content = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk: break
            content.append(chunk)
    return ''.join(content)

user_requests = defaultdict(deque)
def is_rate_limited(user_id: int, max_requests: int = 5) -> bool:
    now = time()
    q = user_requests[user_id]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= max_requests:
        return True
    q.append(now)
    return False

def should_restart():
    runtime_dir = "runtime"
    os.makedirs(runtime_dir, exist_ok=True)
    restart_file = os.path.join(runtime_dir, "last_restart.txt")
    now = time()
    try:
        with open(restart_file, "r") as f:
            last = float(f.read().strip())
        if now - last > 7 * 24 * 3600:
            with open(restart_file, "w") as f:
                f.write(str(now))
            return True
    except:
        with open(restart_file, "w") as f:
            f.write(str(now))
    return False