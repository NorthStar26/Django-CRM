import os
import re

def fix_celery_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace imports
    content = re.sub(r'from\s+celery\s+import\s+Celery', 'from celery import shared_task', content)
    
    # Remove app initialization
    content = re.sub(r'app\s*=\s*Celery\(["\'].*["\']\)[^\n]*\n', '', content)
    
    # Replace @app.task with @shared_task
    content = re.sub(r'@app\.task', '@shared_task', content)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Fixed {file_path}")

def find_and_fix_task_files(base_path):
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file == 'tasks.py' and 'venv' not in root and 'site-packages' not in root:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'app = Celery(' in content:
                        fix_celery_file(file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == '__main__':
    find_and_fix_task_files(".")
