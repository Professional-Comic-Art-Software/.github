#!/usr/bin/env python3
import os
import json
import yaml
import random
import time
import threading
from collections import defaultdict
from datetime import datetime

class ConfigManager:
    def __init__(self):
        self.configs = {}
        self.environments = ['development', 'staging', 'production']
        self.services = ['api', 'web', 'worker', 'scheduler', 'cache', 'database']
        self.regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
        self.versions = defaultdict(int)
        self.history = defaultdict(list)
        self.lock = threading.Lock()
        self.watchers = defaultdict(list)
        
    def generate_config(self, service, environment):
        config = {
            'service': service,
            'environment': environment,
            'version': self.versions[f"{service}_{environment}"] + 1,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'settings': self.generate_settings(service),
            'features': self.generate_features(),
            'limits': self.generate_limits(),
            'endpoints': self.generate_endpoints(service),
            'credentials': self.generate_credentials(),
            'logging': self.generate_logging_config(),
            'monitoring': self.generate_monitoring_config()
        }
        return config
    
    def generate_settings(self, service):
        settings = {
            'api': {
                'host': '0.0.0.0',
                'port': random.choice([3000, 8080, 8000, 5000]),
                'workers': random.randint(2, 8),
                'timeout': random.randint(30, 120),
                'rate_limit': random.randint(100, 1000),
                'cors_enabled': random.choice([True, False])
            },
            'web': {
                'host': '0.0.0.0',
                'port': random.choice([80, 443, 3000]),
                'static_path': '/var/www/static',
                'session_timeout': random.randint(3600, 86400),
                'max_upload_size': random.choice([10485760, 104857600, 1073741824])
            },
            'worker': {
                'concurrency': random.randint(5, 20),
                'max_retries': random.randint(3, 10),
                'queue': f"queue_{service}",
                'prefetch_count': random.randint(5, 50)
            },
            'cache': {
                'max_memory': random.choice(['256mb', '512mb', '1gb', '2gb']),
                'max_keys': random.randint(10000, 100000),
                'eviction_policy': random.choice(['lru', 'lfu', 'ttl']),
                'ttl': random.randint(300, 3600)
            },
            'database': {
                'pool_size': random.randint(10, 50),
                'max_connections': random.randint(50, 200),
                'statement_timeout': random.randint(30000, 60000),
                'idle_timeout': random.randint(10000, 30000)
            }
        }
        return settings.get(service, settings['api'])
    
    def generate_features(self):
        features = {}
        feature_names = [
            'new_dashboard', 'beta_api', 'advanced_search', 'realtime_updates',
            'batch_processing', 'export_data', 'import_data', 'webhooks',
            'sso_integration', 'audit_logs', 'data_retention', 'custom_domains'
        ]
        
        for feature in feature_names:
            features[feature] = {
                'enabled': random.choice([True, False]),
                'rollout_percentage': random.randint(0, 100),
                'description': f"Feature flag for {feature}"
            }
        
        return features
    
    def generate_limits(self):
        return {
            'rate_limit': random.randint(1000, 10000),
            'burst_limit': random.randint(100, 1000),
            'concurrent_requests': random.randint(50, 500),
            'max_file_size': random.choice([10485760, 104857600, 5368709120]),
            'max_batch_size': random.randint(100, 1000),
            'timeout_seconds': random.randint(30, 300)
        }
    
    def generate_endpoints(self, service):
        endpoints = []
        endpoint_templates = {
            'api': ['/v1/users', '/v1/products', '/v1/orders', '/v1/search', '/health'],
            'web': ['/', '/dashboard', '/settings', '/profile', '/login'],
            'worker': ['/jobs', '/queue', '/status', '/metrics'],
            'cache': ['/cache', '/stats', '/flush'],
            'database': ['/query', '/migrate', '/backup', '/restore']
        }
        
        for path in endpoint_templates.get(service, endpoint_templates['api']):
            endpoints.append({
                'path': path,
                'methods': random.sample(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], 
                                       random.randint(1, 3)),
                'auth_required': random.choice([True, False]),
                'rate_limited': random.choice([True, False])
            })
        
        return endpoints
    
    def generate_credentials(self):
        return {
            'api_key': f"key_{random.randint(1000000000, 9999999999):x}",
            'secret_key': f"sec_{random.randint(1000000000, 9999999999):x}",
            'jwt_secret': f"jwt_{random.randint(1000000000, 9999999999):x}",
            'encryption_key': f"enc_{random.randint(1000000000, 9999999999):x}"
        }
    
    def generate_logging_config(self):
        return {
            'level': random.choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
            'format': random.choice(['json', 'text', 'structured']),
            'output': random.choice(['stdout', 'file', 'syslog', 'elasticsearch']),
            'sample_rate': random.random(),
            'include_headers': random.choice([True, False]),
            'include_body': random.choice([True, False])
        }
    
    def generate_monitoring_config(self):
        return {
            'metrics_enabled': True,
            'tracing_enabled': random.choice([True, False]),
            'sampling_rate': random.uniform(0.1, 1.0),
            'exporters': random.sample(['prometheus', 'datadog', 'newrelic', 'jaeger'], 
                                      random.randint(1, 3))
        }
    
    def set_config(self, service, environment, config=None):
        key = f"{service}_{environment}"
        
        with self.lock:
            if config is None:
                config = self.generate_config(service, environment)
            
            self.versions[key] = config['version']
            self.configs[key] = config
            
            history_entry = {
                'version': config['version'],
                'timestamp': time.time(),
                'config': config.copy()
            }
            self.history[key].append(history_entry)
            
            if len(self.history[key]) > 20:
                self.history[key] = self.history[key][-20:]
            
            self.notify_watchers(key, config)
            
        return config
    
    def get_config(self, service, environment, version=None):
        key = f"{service}_{environment}"
        
        if version is not None:
            for entry in self.history[key]:
                if entry['version'] == version:
                    return entry['config']
            return None
        
        return self.configs.get(key)
    
    def watch_config(self, key, callback):
        self.watchers[key].append(callback)
    
    def notify_watchers(self, key, config):
        for callback in self.watchers[key]:
            try:
                callback(config)
            except:
                pass
    
    def delete_config(self, service, environment):
        key = f"{service}_{environment}"
        with self.lock:
            if key in self.configs:
                del self.configs[key]
                return True
        return False
    
    def list_configs(self):
        configs = []
        for key, config in self.configs.items():
            configs.append({
                'key': key,
                'service': config['service'],
                'environment': config['environment'],
                'version': config['version'],
                'updated_at': config['updated_at']
            })
        return configs
    
    def validate_config(self, config):
        required_fields = ['service', 'environment', 'version', 'settings']
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        return True, "Valid"
    
    def export_config(self, service, environment, format='json'):
        config = self.get_config(service, environment)
        
        if config is None:
            return None
        
        if format == 'json':
            return json.dumps(config, indent=2)
        elif format == 'yaml':
            return yaml.dump(config)
        else:
            return config
    
    def import_config(self, data, format='json'):
        try:
            if format == 'json':
                config = json.loads(data)
            elif format == 'yaml':
                config = yaml.safe_load(data)
            else:
                return None
            
            valid, message = self.validate_config(config)
            if not valid:
                return {'error': message}
            
            result = self.set_config(
                config['service'],
                config['environment'],
                config
            )
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def run_simulation(self):
        for _ in range(20):
            service = random.choice(self.services)
            env = random.choice(self.environments)
            region = random.choice(self.regions)
            
            config = self.generate_config(service, env)
            config['region'] = region
            self.set_config(service, env, config)
            
            time.sleep(random.uniform(0.01, 0.05))
        
        return self.list_configs()

def main():
    cm = ConfigManager()
    configs = cm.run_simulation()
    print(f"Config manager: {len(configs)} configurations managed")

if __name__ == "__main__":
    main()