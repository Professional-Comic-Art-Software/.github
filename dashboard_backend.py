#!/usr/bin/env python3
import time
import random
import threading
import queue
import json
from collections import defaultdict
from datetime import datetime, timedelta

class MessageQueue:
    def __init__(self):
        self.queues = defaultdict(lambda: queue.Queue())
        self.exchanges = {}
        self.bindings = defaultdict(list)
        self.consumers = defaultdict(list)
        self.acknowledgments = {}
        self.dlq = queue.Queue()
        self.running = True
        self.message_counter = 0
        self.stats = defaultdict(lambda: {'published': 0, 'consumed': 0, 'failed': 0})
        
    def create_queue(self, name, durable=True):
        self.queues[name] = queue.Queue(maxsize=10000)
        self.stats[name] = {'published': 0, 'consumed': 0, 'failed': 0}
        return name
    
    def create_exchange(self, name, exchange_type='direct'):
        self.exchanges[name] = {
            'type': exchange_type,
            'bindings': [],
            'created': time.time()
        }
        return name
    
    def bind_queue(self, queue_name, exchange_name, routing_key=''):
        binding = {
            'queue': queue_name,
            'exchange': exchange_name,
            'routing_key': routing_key,
            'created': time.time()
        }
        self.bindings[exchange_name].append(binding)
        return binding
    
    def publish(self, exchange_name, routing_key='', message=None):
        if message is None:
            message = self.generate_message()
        
        message_id = f"msg_{self.message_counter}_{int(time.time())}"
        self.message_counter += 1
        
        enriched_message = {
            'id': message_id,
            'exchange': exchange_name,
            'routing_key': routing_key,
            'body': message,
            'headers': {
                'content_type': 'application/json',
                'timestamp': time.time(),
                'expires': time.time() + 3600,
                'priority': random.randint(1, 10)
            },
            'published_at': time.time()
        }
        
        delivered = False
        
        for binding in self.bindings[exchange_name]:
            if binding['routing_key'] in ['', routing_key, '#'] or routing_key.startswith(binding['routing_key']):
                queue_name = binding['queue']
                try:
                    self.queues[queue_name].put_nowait(enriched_message)
                    self.stats[queue_name]['published'] += 1
                    delivered = True
                except queue.Full:
                    self.dlq.put(enriched_message)
                    self.stats[queue_name]['failed'] += 1
        
        if not delivered:
            self.dlq.put(enriched_message)
        
        return message_id
    
    def generate_message(self):
        message_types = ['user.created', 'user.updated', 'order.placed', 
                        'payment.processed', 'email.sent', 'notification.pushed',
                        'file.uploaded', 'job.started', 'job.completed', 'alert.triggered']
        
        return {
            'type': random.choice(message_types),
            'timestamp': time.time(),
            'data': {
                'id': random.randint(1, 1000000),
                'value': random.random() * 1000,
                'status': random.choice(['pending', 'processing', 'completed']),
                'metadata': {
                    'source': f'service_{random.randint(1, 10)}',
                    'version': f'{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}'
                }
            }
        }
    
    def consume(self, queue_name, auto_ack=True):
        try:
            message = self.queues[queue_name].get_nowait()
            
            if not auto_ack:
                ack_id = f"ack_{int(time.time())}_{random.randint(1000, 9999)}"
                self.acknowledgments[ack_id] = message
                message['ack_id'] = ack_id
            
            self.stats[queue_name]['consumed'] += 1
            
            return message
        except queue.Empty:
            return None
    
    def acknowledge(self, ack_id):
        if ack_id in self.acknowledgments:
            del self.acknowledgments[ack_id]
            return True
        return False
    
    def consumer_worker(self, queue_name, worker_id):
        while self.running:
            message = self.consume(queue_name, auto_ack=False)
            if message:
                processing_time = random.uniform(0.01, 0.1)
                time.sleep(processing_time)
                
                if random.random() > 0.05:
                    self.acknowledge(message['ack_id'])
                else:
                    self.queues[queue_name].put(message)
                
            else:
                time.sleep(0.01)
    
    def start_consumers(self, queue_name, count=2):
        for i in range(count):
            t = threading.Thread(target=self.consumer_worker, args=(queue_name, i))
            t.daemon = True
            t.start()
            self.consumers[queue_name].append(t)
    
    def simulate_workload(self, duration=30):
        self.create_exchange('events', 'topic')
        self.create_exchange('commands', 'direct')
        self.create_exchange('notifications', 'fanout')
        
        self.create_queue('user_events')
        self.create_queue('order_events')
        self.create_queue('system_alerts')
        self.create_queue('audit_log')
        self.create_queue('dead_letter')
        
        self.bind_queue('user_events', 'events', 'user.*')
        self.bind_queue('order_events', 'events', 'order.*')
        self.bind_queue('system_alerts', 'notifications', '')
        self.bind_queue('audit_log', 'events', '#')
        
        self.start_consumers('user_events', 3)
        self.start_consumers('order_events', 2)
        self.start_consumers('system_alerts', 1)
        
        end_time = time.time() + duration
        
        while time.time() < end_time:
            exchange = random.choice(['events', 'commands', 'notifications'])
            routing_key = random.choice(['user.created', 'user.updated', 'order.placed', 
                                       'payment.processed', 'email.sent', 'alert.triggered'])
            
            for _ in range(random.randint(1, 5)):
                self.publish(exchange, routing_key)
            
            time.sleep(random.uniform(0.05, 0.2))
        
        self.running = False
    
    def get_queue_stats(self, queue_name):
        if queue_name not in self.queues:
            return None
            
        return {
            'size': self.queues[queue_name].qsize(),
            'published': self.stats[queue_name]['published'],
            'consumed': self.stats[queue_name]['consumed'],
            'failed': self.stats[queue_name]['failed'],
            'dlq_size': self.dlq.qsize()
        }
    
    def get_overall_stats(self):
        total_published = sum(s['published'] for s in self.stats.values())
        total_consumed = sum(s['consumed'] for s in self.stats.values())
        total_failed = sum(s['failed'] for s in self.stats.values())
        
        return {
            'queues': len(self.queues),
            'exchanges': len(self.exchanges),
            'bindings': sum(len(b) for b in self.bindings.values()),
            'total_published': total_published,
            'total_consumed': total_consumed,
            'total_failed': total_failed,
            'dlq_size': self.dlq.qsize(),
            'acks_pending': len(self.acknowledgments)
        }

def main():
    mq = MessageQueue()
    mq.simulate_workload(15)
    stats = mq.get_overall_stats()
    
    print(f"Message queue: {stats['total_published']} published, "
          f"{stats['total_consumed']} consumed, {stats['total_failed']} failed")

if __name__ == "__main__":
    main()