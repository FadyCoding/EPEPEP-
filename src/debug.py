import os


print(os.listdir())
json_file_path = "data/cloned_repos.json"

if os.path.exists(json_file_path):
    print(f"File exists: {json_file_path}")
else:
    print(f"File not found: {json_file_path}")

try:
    with open(json_file_path, 'r') as file:
        data = file.read()
        print("File content loaded successfully.")
        print(data)
except Exception as e:
    print(f"Error reading the file: {e}")
    exit(1)
