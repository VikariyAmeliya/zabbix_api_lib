from zabbix_api import API
from pathlib import Path
import os
import json
import time


class ZabbixCache:
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
        if self.pid_file.exists():
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
            
            work = {
                'users': {},
                'hg_available': {},
                'host': {}
            }
            
            try:
                work['users'] = self.api.get_usergroup()
                work['hg_available'] = self.api.get_hostgroup_list_v64()
                work['host'] = self.api.get_hostgroup_hosts_v64(groups=work['hg_available'])
                
                if 'array' in work['host']:
                    for hostid in work['host']['all'].keys():
                        tags = self.api.get_host_tags([hostid])
                        if tags and 'host' in tags and hostid in tags['host']:
                            work['host']['all'][hostid]['tags'] = tags['host'][hostid]('tags', {})
                             
                with open(self.cache_file, 'w') as f:
                    json.dump(work, f, indent=2)
                    
                exec_time = time.time() - start_time
                print(f" {exec_time} seconds")
                return True
            
            except Exception as e:
                print(f"Ошибка при создании кэша: {e}")
                return False
            
        finally:
            self._remove_pid()
            print("PID-файл удален")

           
 
            
        
        
        
