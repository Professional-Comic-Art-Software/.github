#!/usr/bin/env python3
import time
import random
import threading
import heapq
from collections import deque, defaultdict
from datetime import datetime

class LoadBalancer:
    def __init__(self):
        self.servers = []
        self.health_checks = {}
        self.routing_table = {}
        self.algorithms = ['round_robin', 'least_connections', 'random', 'weighted', 'ip_hash']
        self.algorithm = random.choice(self.algorithms)
        self.current_index = 0
        self.lock = threading.Lock()
        self.request_log = deque(maxlen=10000)
        
    def add_server(self, host, port, weight=1):
        server_id = f"{host}:{port}"
        server = {
            'id': server_id,
            'host': host,
            'port': port,
            'weight': weight,
            'connections': 0,
            'requests': 0,
            'errors': 0,
            'latency': [],
            'healthy': True,
            'last_check': time.time(),
            'added_at': time.time()
        }
        self.servers.append(server)
        return server_id
    
    def generate_server_pool(self, count=5):
        hosts = ['web1', 'web2', 'web3', 'app1', 'app2', 'api1', 'api2', 'cache1', 'db1']
        domains = ['internal', 'cluster.local', 'service.consul', 'backend.svc']
        
        for i in range(count):
            host = f"{random.choice(hosts)}-{i}.{random.choice(domains)}"
            port = random.choice([80, 443, 3000, 8080, 8443])
            weight = random.randint(1, 5)
            self.add_server(host, port, weight)
    
    def round_robin(self):
        with self.lock:
            healthy_servers = [s for s in self.servers if s['healthy']]
            if not healthy_servers:
                return None
            
            self.current_index = (self.current_index + 1) % len(healthy_servers)
            return healthy_servers[self.current_index]
    
    def least_connections(self):
        with self.lock:
            healthy_servers = [s for s in self.servers if s['healthy']]
            if not healthy_servers:
                return None
            
            return min(healthy_servers, key=lambda s: s['connections'])
    
    def random_server(self):
        with self.lock:
            healthy_servers = [s for s in self.servers if s['healthy']]
            if not healthy_servers:
                return None
            
            return random.choice(healthy_servers)
    
    def weighted_random(self):
        with self.lock:
            healthy_servers = [s for s in self.servers if s['healthy']]
            if not healthy_servers:
                return None
            
            weights = [s['weight'] for s in healthy_servers]
            total = sum(weights)
            r = random.uniform(0, total)
            
            cumsum = 0
            for server, weight in zip(healthy_servers, weights):
                cumsum += weight
                if r <= cumsum:
                    return server
            
            return healthy_servers[0]
    
    def ip_hash(self, client_ip):
        with self.lock:
            healthy_servers = [s for s in self.servers if s['healthy']]
            if not healthy_servers:
                return None
            
            hash_val = hash(client_ip) % len(healthy_servers)
            return healthy_servers[hash_val]
    
    def get_server(self, client_ip=None):
        if self.algorithm == 'round_robin':
            return self.round_robin()
        elif self.algorithm == 'least_connections':
            return self.least_connections()
        elif self.algorithm == 'random':
            return self.random_server()
        elif self.algorithm == 'weighted':
            return self.weighted_random()
        elif self.algorithm == 'ip_hash' and client_ip:
            return self.ip_hash(client_ip)
        else:
            return self.round_robin()
    
    def handle_request(self, client_ip=None):
        server = self.get_server(client_ip)
        
        if not server:
            return {'error': 'no healthy servers'}
        
        server['connections'] += 1
        server['requests'] += 1
        
        start_time = time.time()
        
        latency = random.uniform(5, 100)
        time.sleep(latency / 1000)
        
        success = random.random() > 0.05
        status_code = 200 if success else random.choice([500, 502, 503, 504])
        
        if not success:
            server['errors'] += 1
        
        server['connections'] -= 1
        server['latency'].append(latency)
        
        if len(server['latency']) > 100:
            server['latency'] = server['latency'][-100:]
        
        request_log = {
            'timestamp': time.time(),
            'client': client_ip or f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
            'server': server['id'],
            'latency': latency,
            'status': status_code,
            'algorithm': self.algorithm
        }
        
        self.request_log.append(request_log)
        
        return request_log
    
    def health_check(self):
        for server in self.servers:
            if time.time() - server['last_check'] > 5:
                server['healthy'] = random.random() > 0.1
                server['last_check'] = time.time()
    
    def get_server_stats(self, server_id):
        for server in self.servers:
            if server['id'] == server_id:
                return {
                    'id': server['id'],
                    'healthy': server['healthy'],
                    'requests': server['requests'],
                    'errors': server['errors'],
                    'error_rate': server['errors'] / max(server['requests'], 1),
                    'avg_latency': sum(server['latency']) / max(len(server['latency']), 1),
                    'connections': server['connections']
                }
        return None
    
    def get_overall_stats(self):
        total_requests = sum(s['requests'] for s in self.servers)
        total_errors = sum(s['errors'] for s in self.servers)
        healthy_count = sum(1 for s in self.servers if s['healthy'])
        
        return {
            'algorithm': self.algorithm,
            'total_servers': len(self.servers),
            'healthy_servers': healthy_count,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': total_errors / max(total_requests, 1),
            'requests_logged': len(self.request_log)
        }
    
    def simulate_traffic(self, duration=30):
        end_time = time.time() + duration
        
        while time.time() < end_time:
            self.health_check()
            
            client_ip = f"{random.randint(1,254)}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}"
            
            for _ in range(random.randint(1, 10)):
                self.handle_request(client_ip)
            
            time.sleep(random.uniform(0.01, 0.1))
    
    def change_algorithm(self):
        self.algorithm = random.choice([a for a in self.algorithms if a != self.algorithm])

def main():
    lb = LoadBalancer()
    lb.generate_server_pool(8)
    
    print(f"Starting load balancer with {len(lb.servers)} servers, algorithm: {lb.algorithm}")
    
    for i in range(3):
        lb.change_algorithm()
        lb.simulate_traffic(5)
    
    stats = lb.get_overall_stats()
    print(f"Load balancer: {stats['total_requests']} requests, "
          f"error rate: {stats['error_rate']:.2%}")

if __name__ == "__main__":
    main()