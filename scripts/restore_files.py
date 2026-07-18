import os
import shutil
import httpx

SONAR_TOKEN = "squ_d7721e5bb7a3ae4ee9b42fd5d876dfbdd45c6f36"
SONAR_URL = "http://localhost:9000"
PROJECT_ROOT = "/home/grzegorz/cloud/dreamsoft_factory/backend"
DOCKERIZED_ROOT = "/home/grzegorz/cloud/dreamsoft_factory/Dockerized/backend"

def main():
    url = f"{SONAR_URL}/api/issues/search"
    params = {
        "componentKeys": "backend",
        "resolved": "false",
        "types": "BUG",
        "severities": "CRITICAL,BLOCKER,MAJOR",
        "ps": 100
    }
    headers = {"Authorization": f"Bearer {SONAR_TOKEN}"}

    try:
        resp = httpx.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"Błąd SonarQube: {resp.text}")
            return
            
        issues = resp.json().get("issues", [])
        files_restored = set()

        for issue in issues:
            comp = issue["component"]
            if ":" in comp:
                file_path = comp.split(":", 1)[1]
            else:
                file_path = comp
            
            host_path = os.path.join(PROJECT_ROOT, file_path)
            dockerized_path = os.path.join(DOCKERIZED_ROOT, file_path)
            
            if os.path.exists(dockerized_path):
                shutil.copy2(dockerized_path, host_path)
                files_restored.add(host_path)

        print(f"Pomyślnie przywrócono {len(files_restored)} plików z Dockerized:")
        for f in files_restored:
            print(f" - {f}")
    except Exception as e:
        print(f"Błąd przywracania: {e}")

if __name__ == "__main__":
    main()
