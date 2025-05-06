import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time
from zabbix_api import API  
class ZabbixEventCache:
    def __init__(self, api, cache_dir, pid_dir, days_to_cache=30, time_delta=10800):
        
        self.api = api
        self.cache_dir = Path(cache_dir)
        self.pid_dir = Path(pid_dir)
        self.days_to_cache = days_to_cache
        self.time_delta = time_delta
        self.current_time = int(time.time())
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "zabbix_local.cache"
        self.pid_file = self.pid_dir / "cron_make_cache.pid"
        
    def _check_pid(self):
        pid_file = self.pid_dir / "_cron_event_cache.pid"
        if pid_file.exists():
            print(f"Процесс уже запущен PID-файл {pid_file} существует")
            return True
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        return False

    def _remove_pid(self):
        pid_file = self.pid_dir / "_cron_event_cache.pid"
        if pid_file.exists():
            pid_file.unlink()

    def run(self):
        if self._check_pid():
            return False

        try:
            for day in range(1, self.days_to_cache + 1):
                day_unixtime = self._get_day_start_unixtime(day)
                self._process_day(day_unixtime)
        finally:
            self._remove_pid()

    def _get_day_start_unixtime(self, days_ago):
        day_date = datetime.now() - timedelta(days=days_ago)
        day_start = datetime(day_date.year, day_date.month, day_date.day)
        return int(day_start.timestamp()) + self.time_delta

    def _process_day(self, day_unixtime):
        day_end_unixtime = day_unixtime + 86400  # +24 часа
        cache_file = self.cache_dir / f"events-{datetime.fromtimestamp(day_unixtime).strftime('%Y-%m-%d')}.json"

        # Если файл уже есть проверяем его 
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                if isinstance(data.get('event'), dict):
                    print(f"Файл {cache_file} уже существует и валиден.")
                    return
            except json.JSONDecodeError:
                print(f"Файл {cache_file} битый, пересоздаём.")

        events = self._get_events(day_unixtime, day_end_unixtime)
        if not events:
            print(f"Нет событий за {datetime.fromtimestamp(day_unixtime).strftime('%Y-%m-%d')}.")
            return

        with open(cache_file, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"Создан кэш для {datetime.fromtimestamp(day_unixtime).strftime('%Y-%m-%d')}.")

    def _get_events(self, time_from, time_till):
        problem_events = self.api.do('event.get', {
            'value': 1,
            'time_from': time_from,
            'time_till': time_till,
            'min_severity': 1,
            'selectHosts': 'extend',
            'selectTags': 'extend',
            'select_acknowledges': 'extend'
        }) or []

        #Получаем события о восстановлении value=0
        recovery_event_ids = [event['r_eventid'] for event in problem_events if 'r_eventid' in event]
        recovery_events = self.api.do('event.get', {
            'value': 0,
            'eventids': recovery_event_ids
        }) if recovery_event_ids else []

        #Связываем проблемы и восстановления
        events = {}
        for event in problem_events:
            event_id = event['eventid']
            events[event_id] = {
                'name': event['name'],
                'clock': event['clock'] - self.time_delta,
                'objectid': event['objectid'],
                'severity': event['severity'],
                'value': 1,  # Проблема
                'hosts': event.get('hosts', []),
                'tags': event.get('tags', []),
                'acknowledged': event.get('acknowledged', 0)
            }

            #Если есть событие восстановления
            if 'r_eventid' in event:
                recovery = next((e for e in recovery_events if e['eventid'] == event['r_eventid']), None)
                if recovery:
                    events[event_id]['recovery_event'] = {
                        'eventid': recovery['eventid'],
                        'clock': recovery['clock'] - self.time_delta,
                        'value': 0  #восстановление
                    }
                    #Считаем длительность проблемы
                    events[event_id]['duration'] = recovery['clock'] - event['clock']

        return {'event': events}

