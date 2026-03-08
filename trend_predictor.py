#!/usr/bin/env python3
import time
import random
import threading
import socket
import json
from datetime import datetime
from collections import defaultdict

class HealthChecker:
    def __init__(self):
        self.services = {}
        self.checks = []
        self.results = defaultdict(list)
        self.statuses = {}
        self.running = True
        self.check_interval = 5
        self.timeout = 2
        self.thresholds = {
            'cpu': 80,
            'memory': 85,
            'disk': 90,
            'latency': 500
        }
        
    def register_service(self, name, host, port, check_type='http'):
        service_id = f"{name}_{host}_{port}"
        service = {
            'id': service_id,
            'name': name,
            'host': host,
            'port': port,
            'check_type': check_type,
            'registered_at': time.time(),
            'checks_performed': 0,
            'failures': 0,
            'successes': 0,
            'status': 'unknown'
        }
        self.services[service_id] = service
        return service_id
    
    def generate_service_pool(self, count=20):
        service_types = ['api', 'web', 'auth', 'db', 'cache', 'worker', 'scheduler', 'queue']
        domains = ['internal', 'service.local', 'cluster', 'backend']
        
        for i in range(count):
            name = f"{random.choice(service_types)}-{i+1}"
            host = f"{name}.{random.choice(domains)}"
            port = random.choice([80, 443, 3000, 5432, 6379, 8080, 9200, 11211])
            check_type = random.choice(['http', 'tcp', 'grpc', 'custom'])
            self.register_service(name, host, port, check_type)
    
    def perform_http_check(self, service):
        start_time = time.time()
        time.sleep(random.uniform(0.05, 0.3))
        duration = (time.time() - start_time) * 1000
        
        success = random.random() > 0.1
        status_code = 200 if success else random.choice([500, 502, 503, 504])
        
        return {
            'success': success,
            'status_code': status_code,
            'duration': duration,
            'timestamp': time.time()
        }
    
    def perform_tcp_check(self, service):
        start_time = time.time()
        time.sleep(random.uniform(0.01, 0.1))
        duration = (time.time() - start_time) * 1000
        
        success = random.random() > 0.05
        
        return {
            'success': success,
            'duration': duration,
            'timestamp': time.time()
        }
    
    def perform_grpc_check(self, service):
        start_time = time.time()
        time.sleep(random.uniform(0.02, 0.15))
        duration = (time.time() - start_time) * 1000
        
        success = random.random() > 0.08
        
        return {
            'success': success,
            'duration': duration,
            'timestamp': time.time()
        }
    
    def perform_custom_check(self, service):
        metrics = {
            'cpu_usage': random.uniform(10, 90),
            'memory_usage': random.uniform(20, 85),
            'disk_usage': random.uniform(30, 95),
            'connections': random.randint(10, 500)
        }
        
        success = all([
            metrics['cpu_usage'] < self.thresholds['cpu'],
            metrics['memory_usage'] < self.thresholds['memory'],
            metrics['disk_usage'] < self.thresholds['disk']
        ])
        
        return {
            'success': success,
            'metrics': metrics,
            'timestamp': time.time()
        }
    
    def check_service(self, service_id):
        service = self.services.get(service_id)
        if not service:
            return None
        
        check_type = service['check_type']
        
        if check_type == 'http':
            result = self.perform_http_check(service)
        elif check_type == 'tcp':
            result = self.perform_tcp_check(service)
        elif check_type == 'grpc':
            result = self.perform_grpc_check(service)
        else:
            result = self.perform_custom_check(service)
        
        result['service_id'] = service_id
        result['service_name'] = service['name']
        result['check_type'] = check_type
        
        service['checks_performed'] += 1
        
        if result['success']:
            service['successes'] += 1
            service['status'] = 'healthy'
        else:
            service['failures'] += 1
            service['status'] = 'unhealthy'
        
        self.results[service_id].append(result)
        self.statuses[service_id] = result
        
        if len(self.results[service_id]) > 100:
            self.results[service_id] = self.results[service_id][-100:]
        
        return result
    
    def health_check_worker(self):
        while self.running:
            for service_id in self.services:
                self.check_service(service_id)
            time.sleep(self.check_interval)
    
    def start_checks(self):
        self.checker_thread = threading.Thread(target=self.health_check_worker)
        self.checker_thread.daemon = True
        self.checker_thread.start()
    
    def stop_checks(self):
        self.running = False
    
    def get_service_health(self, service_id):
        if service_id not in self.services:
            return None
        
        service = self.services[service_id]
        recent_results = self.results[service_id][-10:]
        
        if not recent_results:
            return {
                'status': 'unknown',
                'service': service['name'],
                'checks_performed': service['checks_performed']
            }
        
        success_rate = sum(1 for r in recent_results if r['success']) / len(recent_results)
        avg_duration = sum(r.get('duration', 0) for r in recent_results if 'duration' in r) / len(recent_results)
        
        return {
            'service_id': service_id,
            'service_name': service['name'],
            'status': service['status'],
            'success_rate': success_rate,
            'avg_duration': avg_duration,
            'checks_performed': service['checks_performed'],
            'failures': service['failures'],
            'successes': service['successes'],
            'last_check': recent_results[-1]['timestamp']
        }
    
    def get_overall_health(self):
        total_services = len(self.services)
        healthy = sum(1 for s in self.services.values() if s['status'] == 'healthy')
        unhealthy = sum(1 for s in self.services.values() if s['status'] == 'unhealthy')
        unknown = total_services - healthy - unhealthy
        
        return {
            'total_services': total_services,
            'healthy': healthy,
            'unhealthy': unhealthy,
            'unknown': unknown,
            'health_percentage': (healthy / total_services * 100) if total_services > 0 else 0,
            'timestamp': time.time()
        }
    
    def simulate_outage(self, service_id, duration=5):
        if service_id in self.services:
            service = self.services[service_id]
            original_status = service['status']
            service['status'] = 'unhealthy'
            
            time.sleep(duration)
            
            service['status'] = original_status
    
    def generate_health_report(self):
        report = {
            'generated_at': datetime.now().isoformat(),
            'overall': self.get_overall_health(),
            'services': []
        }
        
        for service_id in self.services:
            health = self.get_service_health(service_id)
            if health:
                report['services'].append(health)
        
        return report
    
    def find_unhealthy_services(self):
        return [s for s in self.services.values() if s['status'] == 'unhealthy']
    
    def calculate_uptime(self, service_id, hours=24):
        if service_id not in self.results:
            return None
        
        results = self.results[service_id]
        cutoff = time.time() - (hours * 3600)
        recent = [r for r in results if r['timestamp'] > cutoff]
        
        if not recent:
            return 0
        
        successful = sum(1 for r in recent if r['success'])
        return (successful / len(recent)) * 100

def main():
    checker = HealthChecker()
    checker.generate_service_pool(25)
    checker.start_checks()
    
    time.sleep(15)
    
    report = checker.generate_health_report()
    checker.stop_checks()
    
    print(f"Health checker: {report['overall']['healthy']}/{report['overall']['total_services']} healthy "
          f"({report['overall']['health_percentage']:.1f}%)")

if __name__ == "__main__":
    main()