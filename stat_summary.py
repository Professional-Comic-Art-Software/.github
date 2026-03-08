#!/usr/bin/env python3
import time
import random
import threading
import queue
from datetime import datetime, timedelta
from collections import deque
import heapq

class TaskScheduler:
    def __init__(self):
        self.task_queue = queue.PriorityQueue()
        self.completed_tasks = deque(maxlen=1000)
        self.failed_tasks = deque(maxlen=500)
        self.running_tasks = {}
        self.workers = []
        self.running = True
        self.task_counter = 0
        self.worker_count = 3
        
    class Task:
        def __init__(self, task_id, name, priority, scheduled_time=None):
            self.task_id = task_id
            self.name = name
            self.priority = priority
            self.scheduled_time = scheduled_time or time.time()
            self.created_at = time.time()
            self.started_at = None
            self.completed_at = None
            self.status = 'pending'
            self.result = None
            self.error = None
            self.retries = 0
            self.max_retries = 3
            
        def __lt__(self, other):
            return self.priority < other.priority
            
        def to_dict(self):
            return {
                'id': self.task_id,
                'name': self.name,
                'priority': self.priority,
                'scheduled': self.scheduled_time,
                'status': self.status,
                'retries': self.retries,
                'duration': (self.completed_at - self.started_at) if self.completed_at and self.started_at else None
            }
    
    def add_task(self, name, priority=5, delay=0):
        self.task_counter += 1
        task_id = f"task_{self.task_counter}_{int(time.time())}"
        scheduled_time = time.time() + delay
        
        task = self.Task(task_id, name, priority, scheduled_time)
        self.task_queue.put((priority, task))
        
        return task_id
    
    def generate_random_tasks(self, count=50):
        task_names = [
            'backup_database', 'cleanup_temp', 'sync_repositories',
            'index_documents', 'generate_reports', 'send_notifications',
            'process_webhooks', 'archive_logs', 'update_search_index',
            'validate_schemas', 'compress_assets', 'scan_security',
            'optimize_images', 'cache_warmup', 'health_check'
        ]
        
        for i in range(count):
            name = random.choice(task_names)
            priority = random.randint(1, 10)
            delay = random.uniform(0, 5)
            self.add_task(name, priority, delay)
    
    def worker_function(self, worker_id):
        while self.running:
            try:
                priority, task = self.task_queue.get(timeout=1)
                
                if task.scheduled_time > time.time():
                    self.task_queue.put((priority, task))
                    time.sleep(0.1)
                    continue
                
                task.status = 'running'
                task.started_at = time.time()
                task.worker_id = worker_id
                
                self.running_tasks[task.task_id] = task
                
                try:
                    result = self.execute_task(task)
                    task.status = 'completed'
                    task.completed_at = time.time()
                    task.result = result
                    
                    self.completed_tasks.append({
                        'task': task.to_dict(),
                        'result': result,
                        'worker': worker_id
                    })
                    
                except Exception as e:
                    task.status = 'failed'
                    task.error = str(e)
                    task.retries += 1
                    
                    if task.retries < task.max_retries:
                        task.priority = max(1, task.priority - 1)
                        self.task_queue.put((priority, task))
                    else:
                        self.failed_tasks.append(task.to_dict())
                
                finally:
                    if task.task_id in self.running_tasks:
                        del self.running_tasks[task.task_id]
                
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
    
    def execute_task(self, task):
        task_type = task.name
        
        if 'backup' in task_type:
            time.sleep(random.uniform(0.5, 2))
            return f"Backup completed: {random.randint(100, 1000)} MB"
            
        elif 'cleanup' in task_type:
            time.sleep(random.uniform(0.3, 1))
            return f"Cleaned: {random.randint(10, 500)} files"
            
        elif 'sync' in task_type:
            time.sleep(random.uniform(0.8, 3))
            return f"Synced: {random.randint(50, 5000)} objects"
            
        elif 'index' in task_type:
            time.sleep(random.uniform(0.6, 2.5))
            return f"Indexed: {random.randint(1000, 50000)} documents"
            
        elif 'generate' in task_type:
            time.sleep(random.uniform(1, 4))
            return f"Generated: {random.randint(1, 20)} reports"
            
        elif 'send' in task_type:
            time.sleep(random.uniform(0.2, 1.5))
            return f"Sent: {random.randint(1, 100)} notifications"
            
        elif 'process' in task_type:
            time.sleep(random.uniform(0.4, 2))
            return f"Processed: {random.randint(5, 500)} webhooks"
            
        elif 'archive' in task_type:
            time.sleep(random.uniform(0.7, 2.8))
            return f"Archived: {random.randint(50, 2000)} files"
            
        elif 'validate' in task_type:
            time.sleep(random.uniform(0.3, 1.2))
            return f"Validated: {random.randint(5, 50)} schemas"
            
        elif 'compress' in task_type:
            time.sleep(random.uniform(0.9, 3.5))
            return f"Compressed: {random.randint(20, 500)} assets"
            
        else:
            time.sleep(random.uniform(0.1, 1))
            return f"Executed: {task.name}"
    
    def start_workers(self):
        for i in range(self.worker_count):
            t = threading.Thread(target=self.worker_function, args=(i,))
            t.daemon = True
            t.start()
            self.workers.append(t)
    
    def stop_workers(self):
        self.running = False
        for w in self.workers:
            w.join(timeout=2)
    
    def get_stats(self):
        return {
            'queue_size': self.task_queue.qsize(),
            'completed_count': len(self.completed_tasks),
            'failed_count': len(self.failed_tasks),
            'running_count': len(self.running_tasks),
            'workers': self.worker_count,
            'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }
    
    def run(self):
        self.start_time = time.time()
        self.generate_random_tasks(200)
        self.start_workers()
        
        time.sleep(10)
        
        self.stop_workers()
        return self.get_stats()

def main():
    scheduler = TaskScheduler()
    stats = scheduler.run()
    print(f"Scheduler completed: {stats['completed_count']} tasks, {stats['failed_count']} failed")

if __name__ == "__main__":
    main()