#!/usr/bin/env python3
import time
import random
import json
import threading
from collections import deque, defaultdict
from datetime import datetime, timedelta

class MetricsCollector:
    def __init__(self):
        self.metrics = defaultdict(lambda: deque(maxlen=1000))
        self.timers = {}
        self.counter = defaultdict(int)
        self.histograms = defaultdict(list)
        self.labels = {}
        self.collecting = True
        self.collection_thread = None
        
    def start_collection(self):
        self.collection_thread = threading.Thread(target=self._collect_loop)
        self.collection_thread.daemon = True
        self.collection_thread.start()
    
    def _collect_loop(self):
        while self.collecting:
            self.collect_system_metrics()
            self.collect_application_metrics()
            self.collect_custom_metrics()
            time.sleep(1)
    
    def collect_system_metrics(self):
        import psutil
        try:
            self.metrics['cpu_percent'].append(psutil.cpu_percent(interval=0.1))
            self.metrics['memory_percent'].append(psutil.virtual_memory().percent)
            self.metrics['disk_usage'].append(psutil.disk_usage('/').percent)
            
            net = psutil.net_io_counters()
            self.metrics['bytes_sent'].append(net.bytes_sent)
            self.metrics['bytes_recv'].append(net.bytes_recv)
            
            self.metrics['connections'].append(len(psutil.net_connections()))
        except:
            self.metrics['cpu_percent'].append(random.uniform(10, 80))
            self.metrics['memory_percent'].append(random.uniform(30, 70))
            self.metrics['disk_usage'].append(random.uniform(40, 90))
    
    def collect_application_metrics(self):
        self.metrics['requests_per_second'].append(random.randint(50, 500))
        self.metrics['error_rate'].append(random.uniform(0, 5))
        self.metrics['response_time'].append(random.uniform(50, 500))
        self.metrics['active_users'].append(random.randint(100, 1000))
        self.metrics['queue_size'].append(random.randint(0, 100))
    
    def collect_custom_metrics(self):
        self.metrics['cache_hits'].append(random.randint(1000, 10000))
        self.metrics['cache_misses'].append(random.randint(100, 1000))
        self.metrics['db_queries'].append(random.randint(500, 5000))
        self.metrics['api_calls'].append(random.randint(200, 2000))
        self.metrics['websocket_connections'].append(random.randint(10, 100))
    
    def increment_counter(self, name, value=1):
        self.counter[name] += value
    
    def start_timer(self, name):
        self.timers[name] = time.time()
    
    def stop_timer(self, name):
        if name in self.timers:
            duration = (time.time() - self.timers[name]) * 1000
            del self.timers[name]
            self.histograms[name].append(duration)
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            return duration
        return None
    
    def record_histogram(self, name, value):
        self.histograms[name].append(value)
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]
    
    def add_label(self, key, value):
        self.labels[key] = value
    
    def get_metric_summary(self, name):
        if name not in self.metrics:
            return None
            
        data = list(self.metrics[name])
        if not data:
            return None
            
        return {
            'current': data[-1] if data else 0,
            'avg': sum(data) / len(data) if data else 0,
            'min': min(data) if data else 0,
            'max': max(data) if data else 0,
            'count': len(data)
        }
    
    def get_histogram_summary(self, name):
        if name not in self.histograms:
            return None
            
        data = self.histograms[name]
        if not data:
            return None
            
        p50 = sorted(data)[len(data) // 2]
        p95 = sorted(data)[int(len(data) * 0.95)]
        p99 = sorted(data)[int(len(data) * 0.99)]
        
        return {
            'count': len(data),
            'min': min(data),
            'max': max(data),
            'avg': sum(data) / len(data),
            'p50': p50,
            'p95': p95,
            'p99': p99
        }
    
    def generate_time_series(self, hours=24):
        series = {}
        now = datetime.now()
        
        for metric_name, values in self.metrics.items():
            timestamps = [(now - timedelta(minutes=i)).isoformat() 
                         for i in range(min(len(values), hours * 60), 0, -1)]
            series[metric_name] = {
                'timestamps': timestamps,
                'values': list(values)[-len(timestamps):]
            }
        
        return series
    
    def export_json(self):
        return {
            'timestamp': datetime.now().isoformat(),
            'counters': dict(self.counter),
            'metrics': {k: list(v) for k, v in self.metrics.items()},
            'histograms': {k: self.get_histogram_summary(k) for k in self.histograms},
            'labels': self.labels
        }
    
    def alert_if_needed(self):
        alerts = []
        
        cpu_avg = self.get_metric_summary('cpu_percent')
        if cpu_avg and cpu_avg['current'] > 80:
            alerts.append(f"High CPU usage: {cpu_avg['current']:.1f}%")
            
        mem_avg = self.get_metric_summary('memory_percent')
        if mem_avg and mem_avg['current'] > 85:
            alerts.append(f"High memory usage: {mem_avg['current']:.1f}%")
            
        rt_avg = self.get_metric_summary('response_time')
        if rt_avg and rt_avg['current'] > 500:
            alerts.append(f"High response time: {rt_avg['current']:.1f}ms")
            
        error_avg = self.get_metric_summary('error_rate')
        if error_avg and error_avg['current'] > 5:
            alerts.append(f"High error rate: {error_avg['current']:.1f}%")
            
        return alerts

def main():
    collector = MetricsCollector()
    collector.add_label('environment', 'development')
    collector.add_label('region', 'us-east-1')
    collector.add_label('service', 'metrics-collector')
    
    collector.start_collection()
    
    for i in range(60):
        collector.increment_counter('api_requests_total')
        collector.start_timer('api_request')
        time.sleep(random.uniform(0.01, 0.1))
        duration = collector.stop_timer('api_request')
        
        if duration:
            collector.record_histogram('api_latency', duration)
            
        collector.record_histogram('random_distribution', random.gauss(50, 15))
        
    summary = collector.export_json()
    alerts = collector.alert_if_needed()
    
    print(f"Metrics collected: {len(summary['metrics'])} metrics, {len(alerts)} alerts")

if __name__ == "__main__":
    main()