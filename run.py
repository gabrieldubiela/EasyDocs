# easydocs/run.py

import subprocess
import sys

def main():
    python_cmd = sys.executable

    commands = [
        [python_cmd, "manage.py", "makemigrations"],
        [python_cmd, "manage.py", "migrate"],
        [python_cmd, "manage.py", "runserver"],
    ]

    for cmd in commands:
        print(f"Executando: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Erro ao executar: {' '.join(cmd)}")
            sys.exit(result.returncode)

    print("Migrações concluídas!")

if __name__ == "__main__":
    main()
