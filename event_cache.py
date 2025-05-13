import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class ZabbixEventCache:
    def __init__(self, api, cache_dir, days_to_cache=30):
        self.api = api
        self.cache_dir = Path(cache_dir)
        self.days_to_cache = days_to_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        for day in range(1, self.days_to_cache + 1):
            day_start = self._get_day_start(day)
            day_end = day_start + 86400  # Добавляем 24 часа
            self._process_day(day_start, day_end)

    #Возвращает начало дня (unixtime) для days_ago дней назад
    def _get_day_start(self, days_ago):
        day_date = datetime.now() - timedelta(days=days_ago)
        return int(datetime(day_date.year, day_date.month, day_date.day).timestamp())
    
    #брабатывает один день проверяет кэш и при необходимости создает
    def _process_day(self, day_start, day_end):
        date_str = datetime.fromtimestamp(day_start).strftime('%Y-%m-%d')
        cache_file = self.cache_dir / f"events-{date_str}.json"

        #Если файл уже существует и валиден - пропускаем
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    json.load(f)
                print(f"Кэш за {date_str} уже существует")
                return
            except (json.JSONDecodeError, IOError):
                print(f"Кэш за {date_str} поврежден, пересоздаем")

        #Получаем события из API
        events = self._get_zabbix_events(day_start, day_end)
        
        if not events:
            print(f"Нет событий за {date_str}")
            return

        # Сохраняем в файл
        with open(cache_file, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"Создан кэш за {date_str}")
        
    #Получаем события из Zabbix API за указанный период
    def _get_zabbix_events(self, time_from, time_till):
        try:
            # Получаем события о проблемах
            problems = self.api.get_events(
                time_from=time_from,
                time_till=time_till,
                value=1,  # Проблемы
                min_severity=1
            )

            if not problems:
                return None

            result = []
            for problem in problems:
                #Преобразуем строки в числа для времени
                problem_clock = int(problem.get('clock', 0))
                
                event_data = {
                    'problem': {
                        'eventid': problem.get('eventid'),
                        'name': problem.get('name'),
                        'clock': problem_clock,
                        'objectid': problem.get('objectid'),
                        'severity': problem.get('severity'),
                        'r_eventid': problem.get('r_eventid')
                    }
                }

                #Если есть событие восстановления
                if 'r_eventid' in problem and problem['r_eventid']:
                    recovery = self._get_recovery_event(problem['r_eventid'])
                    if recovery:
                        recovery_clock = int(recovery.get('clock', 0))
                        event_data['recovery'] = {
                            'eventid': recovery.get('eventid'),
                            'clock': recovery_clock
                        }
                        #Вычисляем продолжительность
                        event_data['duration'] = recovery_clock - problem_clock

                result.append(event_data)

            return result

        except Exception as e:
            print(f"Ошибка при получении событий: {str(e)}")
            return None
        
    #Получает одно событие восстановления по ID
    def _get_recovery_event(self, event_id):
        try:
            recoveries = self.api.get_events(
                eventids=[event_id],
                value=0  #Восстановления
            )
            return recoveries[0] if recoveries else None
        except Exception:
            return None
