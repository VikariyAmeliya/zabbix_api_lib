from ZABBIX_TEST import API
from pathlib import Path
import os
import json
import time


class ZabbixCacheBuilder:
    def __init__(self, api, cache_dir="/Users/whoami?/Documents/_zabbix/cache_structure", 
                 pid_dir="/Users/whoami?/Documents/_zabbix/pid"):

        self.api = api
        self.cache_dir = Path(cache_dir)
        self.pid_dir = Path(pid_dir)
        self.cache_file = self.cache_dir / "zabbix_local.cache"
        self.pid_file = self.pid_dir / "cron_make_cache.pid"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        
    def _check_proc(self):
        if self.pid_file.exists:
            print(f"Процесс уже запущен, файл {self.pid_file} уже существует")
            return True
        return False
    
    def _create_pid(self):
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
            
    def _remove_pid(self):
        if self.pid_file.exists():
            self.pid_file.unlink()
            
    def make_cache(self):
        if self._check_proc():
            return False
        try:
            self._create_pid()
            start_time = time.time()
            users = self.api.get_usergroup()
            hostrgroups = self.api.get_hostgroup_list_v64()
            
        
        
        