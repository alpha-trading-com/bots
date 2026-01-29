import requests
import time
from modules.constants import WEBHOOK_URL_SS_GITHUB_REPOS
from modules.discord import send_webhook_message

def get_latest_commit_sha(github_url):
    """
    Extracts the user and repo from a GitHub URL and fetches the latest commit SHA from the default branch.
    """
    # Example URL: https://github.com/user/repo
    try:
        parts = github_url.rstrip('/').split('/')
        user = parts[-2]
        repo = parts[-1]
        api_url = f"https://api.github.com/repos/{user}/{repo}/commits"
        response = requests.get(api_url)
        if response.status_code != 200:
            print(f"Failed to fetch commits for {github_url}: {response.status_code}")
            return None
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            latest_commit_sha = data[0]['sha']
            return latest_commit_sha
        else:
            print(f"No commits found for {github_url}")
            return None
    except Exception as e:
        print(f"Error processing {github_url}: {e}")
        return None

def monitor_github_repos(url_list, poll_interval=60):
    """
    Periodically checks the GitHub repositories in url_list for new commits.
    """
    latest_shas = {}
    for url in url_list:
        sha = get_latest_commit_sha(url)
        if sha:
            latest_shas[url] = sha
        else:
            latest_shas[url] = None

    print("Started monitoring repositories...")
    while True:
        for url in url_list:
            current_sha = get_latest_commit_sha(url)
            if current_sha and current_sha != latest_shas.get(url):
                print(f"Change detected in {url}!\nNew commit: {current_sha}")
                latest_shas[url] = current_sha
                send_webhook_message(
                    webhook_url=WEBHOOK_URL_SS_GITHUB_REPOS,
                    content=f"Change detected in {url}!\nNew commit: {current_sha}"
                )
        time.sleep(poll_interval)

if __name__ == "__main__":
    # Example usage: provide GitHub URLs here
    github_urls = [
        # "https://github.com/user/repo",
        # Add your target repo URLs here
        "https://github.com/taostat/blockmachine",
        "https://github.com/unconst/eclair"
    ]
    if not github_urls:
        print("No GitHub URLs provided to monitor.")
    else:
        monitor_github_repos(github_urls)
