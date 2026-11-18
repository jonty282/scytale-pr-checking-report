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

pr_number = "999999999999"

url_pr = f"https://api.github.com/repos/home-assistant/frontend/pulls/{pr_number}"
response = requests.get(url_pr, headers=headers)

if response.status_code == 200:
    url_review = f"https://api.github.com/repos/home-assistant/frontend/pulls/{pr_number}/reviews"
    review_reponse = requests.get(url_review, headers=headers)
    
    if review_reponse.status_code == 200:
        data_response_pr = response.json()
        data_response_review = review_reponse.json()

        print(f"Number of reviews for pr {pr_number}: {len(data_response_review)}")

        print(f"pr status: {response.status_code}")
        print(f"review status: {review_reponse.status_code}")

        raw_folder = Path("data/raw")
        raw_folder.mkdir(parents=True, exist_ok=True)

        file_path_pr = raw_folder / f"pr_{pr_number}.json"
        file_path_review = raw_folder / f"review_pr_{pr_number}.json"

        with open(file_path_pr, "w") as f:
            json.dump(data_response_pr, f, indent=2)

        with open(file_path_review, "w") as f:
            json.dump(data_response_review, f, indent=2)
    else:
        print(f"The review for pr {pr_number} failed with a code of {review_reponse.status_code}")
else:
    print(f"pr {pr_number} failed with a code of {response.status_code}.")
    print("Not executed")




