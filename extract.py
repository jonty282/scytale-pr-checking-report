from utils import get_json, save_json
import requests
from pathlib import Path
import sys

def fetch_merged_prs(limit):
    url = "https://api.github.com/repos/home-assistant/frontend/pulls"
    merged_prs = []
    page = 1

    while len(merged_prs) < limit:
        params = {"state": "closed", "base": "dev", "per_page": 100, "page": page}
        prs = get_json(url, params=params)

        if not prs:
            break

        for pr in prs:
            # closed but not merged = skip
            if pr["merged_at"] is not None:
                merged_prs.append(pr)
                if len(merged_prs) == limit:
                    break
        page += 1
    return merged_prs


def fetch_required_checks():
    required = set()

    try:
        rules = get_json("https://api.github.com/repos/home-assistant/frontend/rules/branches/dev")
        for rule in rules:
            if rule["type"] == "required_status_checks":
                for check in rule["parameters"]["required_status_checks"]:
                    required.add(check["context"])
    except requests.exceptions.HTTPError as e:
        print(f"Couldn't get the branch rules: {e}")

    try:
        branch = get_json("https://api.github.com/repos/home-assistant/frontend/branches/dev")
        protection = branch.get("protection") or {}
        status_checks = protection.get("required_status_checks") or {}
        required.update(status_checks.get("contexts") or [])
    except requests.exceptions.HTTPError as e:
        print(f"Couldn't get the branch protection: {e}")

    return sorted(required)


def run_extract(limit):
    raw_folder = Path("data/raw")

    try:
        merged = fetch_merged_prs(limit)
    except requests.exceptions.HTTPError as e:
        print(f"Couldn't fetch the PR list: {e}")
        sys.exit(1)

    print(f"Found {len(merged)} merged PRs")
    save_json(merged, raw_folder / "merged_prs.json")
    save_json(fetch_required_checks(), raw_folder / "required_checks.json")

    failed_prs = []

    for pr in merged:
        try:
            pr_number = pr["number"]

            url_pr = f"https://api.github.com/repos/home-assistant/frontend/pulls/{pr_number}"
            url_review = f"https://api.github.com/repos/home-assistant/frontend/pulls/{pr_number}/reviews"

            pr_data = get_json(url_pr)
            pr_data_review = get_json(url_review, params={"per_page": 100})

            head_sha = pr_data["head"]["sha"]
            url_check_runs =  f"https://api.github.com/repos/home-assistant/frontend/commits/{head_sha}/check-runs"
            url_status =  f"https://api.github.com/repos/home-assistant/frontend/commits/{head_sha}/status"

            pr_data_check_runs = get_json(url_check_runs, params={"per_page": 100})
            pr_data_status = get_json(url_status, params={"per_page": 100})

            print(f"Number of reviews for pr {pr_number}: {len(pr_data_review)}")

            file_path_pr = raw_folder / f"pr_{pr_number}.json"
            file_path_review = raw_folder / f"reviews_{pr_number}.json"
            file_path_check_runs = raw_folder / f"check_runs_{pr_number}.json"
            file_path_status = raw_folder / f"status_{pr_number}.json"


            save_json(pr_data, file_path_pr)
            save_json(pr_data_review, file_path_review)
            save_json(pr_data_check_runs, file_path_check_runs)
            save_json(pr_data_status, file_path_status)
        except requests.exceptions.HTTPError as e:
            print(f"Skipping PR {pr_number}: {e}")
            failed_prs.append(pr_number)
            continue

    save_json(failed_prs, raw_folder / "failed_prs.json")


if __name__ == "__main__":
    run_extract(5)