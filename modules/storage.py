import json
import os
from datetime import datetime

FILE_NAME = "reaction_stats.json"

def save_result(module_name, reaction_time):
    """Сохраняет новый результат в JSON-файл"""
    data = {}
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass

    if module_name not in data:
        data[module_name] = []

    # Добавляем новую запись
    data[module_name].append({
        "date": datetime.now().strftime("%d.%m %H:%M"),
        "reaction_ms": round(reaction_time, 1)
    })

    with open(FILE_NAME, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_results(module_name):
    """Выгружает историю результатов из JSON-файла"""
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(module_name, [])
        except json.JSONDecodeError:
            return []
    return []

def clear_module_history(module_name):
    """Безвозвратно удаляет историю конкретного модуля из файла"""
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if module_name in data:
                data[module_name] = []  # Обнуляем список
                with open(FILE_NAME, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        except json.JSONDecodeError:
            pass