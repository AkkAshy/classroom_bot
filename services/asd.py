import os

full_path = os.path.abspath(r"P:\ClassroomBot\bot\services\credentials.json")
print("Полный путь к файлу:", full_path)
print("Файл существует?", os.path.exists(full_path))


