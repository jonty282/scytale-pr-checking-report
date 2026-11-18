import os, json, requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
github_token = os.getenv("PAT_CODE")

#Githubs standard headers sent for every request
headers = {
    "Authorization": "Bearer " + github_token,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

#gets data from github and turns it into json
def get_json(url, params=None):
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

#saves the data to files
def save_json(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def load_json(file_path):
    with open(file_path) as f:
        return json.load(f)