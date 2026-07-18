import httpx

SONAR_TOKEN = "squ_d7721e5bb7a3ae4ee9b42fd5d876dfbdd45c6f36"
SONAR_URL = "http://localhost:9000"

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
    
    resp = httpx.get(url, params=params, headers=headers)
    issues = resp.json().get("issues", [])
    print(f"Liczba błędów: {len(issues)}")
    
    grouped = {}
    for issue in issues:
        comp = issue["component"].split(":", 1)[1] if ":" in issue["component"] else issue["component"]
        if comp not in grouped:
            grouped[comp] = []
        grouped[comp].append(issue)
        
    for file_path, file_issues in grouped.items():
        print(f"\nPlik: {file_path}")
        for issue in file_issues:
            print(f"  [Linia {issue.get('line')}]: {issue.get('message')}")

if __name__ == "__main__":
    main()
