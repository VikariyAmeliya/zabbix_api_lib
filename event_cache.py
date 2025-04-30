from zabbix_api import API
from pathlib import Path
import os
import json
import time
from datetime import datetime


class ZabbixEventCache:
    def __init__(self, api, cache_dir="/Users/whoami?/Documents/_zabbix/cache_event", 
                 pid_dir="/Users/whoami?/Documents/_zabbix/pid"):
        self.api = api
        self.cache_dir = Path(cache_dir)
        self.pid_dir = Path(pid_dir)
        self.pid_file = self.pid_dir / "cron_event_cache.pid"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pid_dir.mkdir(parents=True, exist_ok=True)
        
        #дата и перевод в UTC+3
        self.make_cache_event_day = 30
        self.time_delta = 10800  # 3 часа

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

    def _get_events(self, time_from, time_till):
        result = {'event': {}}
        
        try:
            #Получаем проблемные события (value=1)
            problem_events = self.api.api.event.get(
                value=1,
                time_from=time_from,
                time_till=time_till,
                min_severity=1,
                selectHosts="extend",
                selectTags="extend",
                select_acknowledges="extend"
            )
            
            r_eventids = []
            for event in problem_events:
                eventid = event['eventid']
                result['event'][eventid] = {
                    'name': event.get('name'),
                    'clock': int(event['clock']) - self.time_delta, #int 
                    'object': event.get('object'),
                    'objectid': event.get('objectid'),
                    'tags': event.get('tags', []),
                    'hosts': event.get('hosts', []),
                    'userid': event.get('userid'),
                    'suppressed': event.get('suppressed'),
                    'value': event.get('value'),
                    'severity': event.get('severity'),
                    'acknowledged': event.get('acknowledged'),
                    'acknowledges': event.get('acknowledges', [])
                }
                
                if event.get('r_eventid'):
                    r_eventids.append(event['r_eventid'])
                    result['event'][eventid]['r_eventid'] = event['r_eventid']

            #Получаем события восстановления (value=0)
            if r_eventids:
                recovery_events = self.api.api.event.get(
                    value=0,
                    eventids=r_eventids,
                    select_acknowledges="extend"
                )
                
                for recovery in recovery_events:
                    for eventid, event_data in result['event'].items():
                        if event_data.get('r_eventid') == recovery['eventid']:
                            event_data['recovery_event'] = {
                                'eventid': recovery['eventid'],
                                'clock': int(recovery['clock']) - self.time_delta,
                                'objectid': recovery.get('objectid'),
                                'object': recovery.get('object'),
                                'userid': recovery.get('userid'),
                                'suppressed': recovery.get('suppressed'),
                                'value': recovery.get('value'),
                                'acknowledged': recovery.get('acknowledged'),
                                'acknowledges': recovery.get('acknowledges', [])
                            }
                            
                            #Рассчитываем длительность проблемы
                            if 'clock' in event_data and 'clock' in event_data['recovery_event']:
                                event_data['duration'] = event_data['recovery_event']['clock'] - event_data['clock']
                            break

        except Exception as e:
            print(f"Ошибка при получении событий: {e}")
            return None
            
        return result

    def _generate_dates(self):
        dates = {}
        current_time = time.time()
        current_day_start = datetime.fromtimestamp(current_time).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp()

        for day in range(1, self.make_cache_event_day + 1):
            day_unixtime = current_day_start - (day * 86400)
            day_date = datetime.fromtimestamp(day_unixtime)
            
            dates[day] = {
                'beginning_day_unixtime': day_unixtime + self.time_delta,
                'end_day_unixtime': day_unixtime + 86399 + self.time_delta,
                'data': day_date.strftime('%Y-%m-%d'),
                'cache_file': self.cache_dir / f"events-{day_date.strftime('%Y-%m-%d')}.json"
            }

        return dates

    def make_cache(self):
        if self._check_proc():
            return False

        try:
            self._create_pid()
            start_time = time.time()
            
            dates = self._generate_dates()

            for day_data in dates.values():
                cache_file = day_data['cache_file']
                time_from = day_data['beginning_day_unixtime']
                time_till = day_data['end_day_unixtime']
                
                if cache_file.exists():
                    try:
                        with open(cache_file, 'r') as f:
                            data = json.load(f)
                        
                        if isinstance(data.get('event'), dict):
                            print(f"Файл {cache_file} уже существует")
                            continue
                    except Exception:
                        print(f"Файл {cache_file} поврежден, пересоздаем")

                event_data = self._get_events(time_from, time_till)
                if event_data:
                    with open(cache_file, 'w') as f:
                        json.dump(event_data, f)
                    print(f"Файл {cache_file} успешно создан")

            exec_time = time.time() - start_time
            print(f"Выполнено за {exec_time} секунд")
            return True

        except Exception as e:
            print(f"Критическая ошибка: {e}")
            return False

        finally:
            self._remove_pid()
            print("PID-файл удален")


