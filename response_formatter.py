#!/usr/bin/env python3
import time
import random
import hashlib
import threading
from collections import OrderedDict, defaultdict
from datetime import datetime

class CacheSimulator:
    def __init__(self, max_size=1000, ttl=300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.access_count = defaultdict(int)
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        self.lock = threading.Lock()
        self.strategies = ['lru', 'lfu', 'fifo', 'ttl']
        self.strategy = random.choice(self.strategies)
        
    def generate_key(self, prefix='cache'):
        return f"{prefix}:{hashlib.md5(str(random.random()).encode()).hexdigest()[:16]}"
    
    def generate_value(self, size=1024):
        return {
            'data': random.getrandbits(size).to_bytes(size//8, 'big').hex()[:size],
            'timestamp': time.time(),
            'metadata': {
                'size': size,
                'encoding': 'utf-8',
                'compressed': random.choice([True, False]),
                'checksum': hashlib.sha256(str(random.random()).encode()).hexdigest()[:16]
            }
        }
    
    def set(self, key, value, custom_ttl=None):
        with self.lock:
            if len(self.cache) >= self.max_size:
                self.evict()
            
            expires = time.time() + (custom_ttl or self.ttl)
            self.cache[key] = {
                'value': value,
                'expires': expires,
                'created': time.time(),
                'accessed': 0,
                'last_access': None
            }
            return True
    
    def get(self, key):
        with self.lock:
            if key not in self.cache:
                self.miss_count += 1
                return None
            
            item = self.cache[key]
            
            if time.time() > item['expires']:
                del self.cache[key]
                self.miss_count += 1
                self.eviction_count += 1
                return None
            
            item['accessed'] += 1
            item['last_access'] = time.time()
            
            if self.strategy == 'lru':
                self.cache.move_to_end(key)
            
            self.hit_count += 1
            self.access_count[key] += 1
            
            return item['value']
    
    def evict(self):
        if not self.cache:
            return None
            
        if self.strategy == 'lru':
            key, _ = self.cache.popitem(last=False)
        elif self.strategy == 'lfu':
            key = min(self.cache.keys(), key=lambda k: self.cache[k]['accessed'])
            del self.cache[key]
        elif self.strategy == 'fifo':
            key = next(iter(self.cache))
            del self.cache[key]
        else:  # ttl
            key = min(self.cache.keys(), key=lambda k: self.cache[k]['expires'])
            del self.cache[key]
        
        self.eviction_count += 1
        return key
    
    def simulate_workload(self, operations=1000):
        read_ratio = 0.7
        write_ratio = 0.2
        delete_ratio = 0.1
        
        keys = []
        
        for i in range(operations):
            r = random.random()
            
            if r < read_ratio and keys:
                key = random.choice(keys)
                self.get(key)
            elif r < read_ratio + write_ratio:
                key = self.generate_key()
                value = self.generate_value(random.randint(128, 4096))
                self.set(key, value)
                keys.append(key)
            else:
                if keys:
                    key = random.choice(keys)
                    with self.lock:
                        if key in self.cache:
                            del self.cache[key]
                    keys.remove(key)
            
            if len(keys) > self.max_size * 1.5:
                keys = keys[:self.max_size]
    
    def get_stats(self):
        total_requests = self.hit_count + self.miss_count
        hit_ratio = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hit_count,
            'misses': self.miss_count,
            'hit_ratio': hit_ratio,
            'evictions': self.eviction_count,
            'strategy': self.strategy,
            'memory_estimate': sum(len(str(v)) for v in self.cache.values())
        }
    
    def warmup(self, count=500):
        for i in range(count):
            key = self.generate_key('warmup')
            value = self.generate_value()
            self.set(key, value, custom_ttl=3600)

def main():
    cache = CacheSimulator(max_size=500, ttl=600)
    cache.warmup(300)
    cache.simulate_workload(5000)
    stats = cache.get_stats()
    
    print(f"Cache simulation: {stats['hits']} hits, {stats['misses']} misses, "
          f"hit ratio: {stats['hit_ratio']:.2%}")

if __name__ == "__main__":
    main()