"""Run a Browser Use cloud task, poll until done, print output, save trace."""
import argparse, json, os, time, requests

API = "https://api.browser-use.com/api/v2"
HEADERS = {"X-Browser-Use-API-Key": os.environ["BROWSER_USE_API_KEY"]}
MAX_POLL_SECONDS = 20 * 60
POLL_INTERVAL = 5
TIMEOUT = (10, 30)

def run(task: str, url: str | None = None) -> dict:
    body = {
        "task": task,
        "sessionSettings": {
            "profileId": os.environ["BROWSER_USE_PROFILE_ID"],
            "proxyCountryCode": "us",
        },
    }
    if url:
        body["startUrl"] = url

    r = requests.post(f"{API}/tasks", json=body, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    task_id = r.json()["id"]
    print(f"Task {task_id} created, polling...")

    deadline = time.time() + MAX_POLL_SECONDS
    while True:
        if time.time() > deadline:
            raise TimeoutError(f"Task {task_id} did not finish within {MAX_POLL_SECONDS}s")
        time.sleep(POLL_INTERVAL)
        r = requests.get(f"{API}/tasks/{task_id}/status", headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        if r.json()["status"] in ("finished", "stopped"):
            break

    r = requests.get(f"{API}/tasks/{task_id}", headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    detail = r.json()

    os.makedirs("browser-use-traces", exist_ok=True)
    with open(f"browser-use-traces/{task_id}.json", "w") as f:
        json.dump(detail, f, indent=2)

    print(f"Status: {detail['status']} | Success: {detail.get('isSuccess')}")
    print(f"Output: {detail.get('output', 'None')}")
    return detail

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("task", help="Task instruction for the browser agent")
    p.add_argument("--url", help="Starting URL", default=None)
    args = p.parse_args()
    run(args.task, args.url)
