# sync_data.py
import os
import subprocess
import json
import sys
from datetime import datetime

def sync_with_github():
    """Синхронизирует данные с GitHub"""
    try:
        # Путь к файлу с данными
        data_file = "members.json"
        
        # Проверяем, есть ли изменения
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if data_file in result.stdout:
            print(f"[{datetime.now()}] Обнаружены изменения в {data_file}, синхронизируем...")
            
            # Добавляем файл
            subprocess.run(["git", "add", data_file], check=True, cwd=os.getcwd())
            
            # Коммитим
            commit_message = f"Auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(["git", "commit", "-m", commit_message], 
                         check=True, cwd=os.getcwd())
            
            # Пушим
            subprocess.run(["git", "push"], check=True, cwd=os.getcwd())
            print(f"[{datetime.now()}] Данные успешно отправлены на GitHub")
        
        # Pull обновлений
        print(f"[{datetime.now()}] Проверяем обновления с GitHub...")
        subprocess.run(["git", "pull"], check=True, cwd=os.getcwd())
        print(f"[{datetime.now()}] Синхронизация завершена")
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка синхронизации: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

if __name__ == "__main__":
    sync_with_github()