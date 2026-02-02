import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from modules.constants import WEBHOOK_URL_SS_GITHUB_REPOS
from modules.discord import send_webhook_message

# Create a session with retry strategy
def create_session():
    """Create a requests session with retry strategy and timeout"""
    session = requests.Session()
    
    # Define retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
        allowed_methods=["GET"]  # Only retry GET requests
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Create a global session for reuse
_session = create_session()

def get_latest_commit_sha(github_url, max_retries=3):
    """
    Extracts the user and repo from a GitHub URL and fetches the latest commit SHA from the default branch.
    Includes retry logic with exponential backoff for network errors.
    """
    # Example URL: https://github.com/user/repo
    parts = github_url.rstrip('/').split('/')
    user = parts[-2]
    repo = parts[-1]
    api_url = f"https://api.github.com/repos/{user}/{repo}/commits"
    
    for attempt in range(max_retries):
        try:
            # Use session with timeout and retry strategy
            response = _session.get(api_url, timeout=(10, 30))  # (connect timeout, read timeout)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited for {github_url}. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            
            if response.status_code != 200:
                print(f"Failed to fetch commits for {github_url}: {response.status_code}")
                if response.status_code >= 500:
                    # Server error, retry
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                return None
            
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                latest_commit_sha = data[0]['sha']
                return latest_commit_sha
            else:
                print(f"No commits found for {github_url}")
                return None
                
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                requests.exceptions.SSLError,
                requests.exceptions.RequestException) as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                print(f"Network error processing {github_url}: {e}")
                print(f"Retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"Error processing {github_url} after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            print(f"Unexpected error processing {github_url}: {e}")
            return None
    
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
        try:
            for url in url_list:
                try:
                    current_sha = get_latest_commit_sha(url)
                    if current_sha and current_sha != latest_shas.get(url):
                        print(f"Change detected in {url}!\nNew commit: {current_sha}")
                        latest_shas[url] = current_sha
                        send_webhook_message(
                            webhook_url=WEBHOOK_URL_SS_GITHUB_REPOS,
                            content=f"Change detected in {url}!\nNew commit: {current_sha}"
                        )
                    elif current_sha:
                        # Update the SHA even if it hasn't changed (in case it was None before)
                        latest_shas[url] = current_sha
                except Exception as e:
                    print(f"Error monitoring {url}: {e}")
                    # Continue with other URLs even if one fails
                    continue
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
        
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
