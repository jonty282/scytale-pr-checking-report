from utils import load_json, save_json
from pathlib import Path
from datetime import datetime
import csv

PASSING_CONCLUSIONS = {"success", "neutral", "skipped"}


def parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check_reviews(reviews, author, merged_at):
    latest_verdict = {}

    for review in sorted(reviews, key=lambda r: r.get("submitted_at") or ""):
        reviewer = (review.get("user") or {}).get("login")
        submitted_at = parse_time(review.get("submitted_at"))

        if reviewer is None or reviewer == author:
            continue
        if submitted_at is None or submitted_at > merged_at:
            continue
        if review["state"] == "COMMENTED":
            continue

        latest_verdict[reviewer] = review["state"]

    approvers = sorted(name for name, verdict in latest_verdict.items() if verdict == "APPROVED")
    return len(approvers) > 0, approvers


def collect_checks(check_runs_data, status_data):
    checks = {}

    for run in check_runs_data.get("check_runs", []):
        name = run["name"]
        started_at = parse_time(run.get("started_at"))
        if name in checks and checks[name]["started_at"] and started_at and started_at < checks[name]["started_at"]:
            continue
        checks[name] = {
            "passed": run["status"] == "completed" and run["conclusion"] in PASSING_CONCLUSIONS,
            "started_at": started_at,
            "finished_at": parse_time(run.get("completed_at")),
        }

    for status in status_data.get("statuses", []):
        checks[status["context"]] = {
            "passed": status["state"] == "success",
            "started_at": parse_time(status.get("created_at")),
            "finished_at": parse_time(status.get("updated_at")),
        }

    return checks


def check_status_checks(checks, required, merged_at):
    names_to_check = required if required else sorted(checks)
    if not names_to_check:
        return False, ["no checks found"]

    problems = []
    for name in names_to_check:
        check = checks.get(name)
        if check is None:
            problems.append(f"{name} (missing)")
        elif check["finished_at"] is None:
            problems.append(f"{name} (never finished)")
        elif not check["passed"]:
            problems.append(f"{name} (failed)")
        elif check["finished_at"] > merged_at:
            problems.append(f"{name} (finished after merge)")

    return len(problems) == 0, problems


def build_row(pr, required, failed_prs, raw_folder):
    pr_number = pr["number"]
    row = {
        "pr_number": pr_number,
        "pr_title": pr["title"],
        "author": (pr.get("user") or {}).get("login", "ghost"),
        "merge_date": pr["merged_at"],
        "CR_Passed": "UNKNOWN",
        "CHECKS_PASSED": "UNKNOWN",
        "approvers": "",
        "check_problems": "",
        "checks_basis": "required" if required else "all checks on head commit",
    }

    if pr_number in failed_prs:
        row["check_problems"] = "data could not be downloaded"
        return row

    merged_at = parse_time(pr["merged_at"])
    reviews = load_json(raw_folder / f"reviews_{pr_number}.json")
    check_runs = load_json(raw_folder / f"check_runs_{pr_number}.json")
    status = load_json(raw_folder / f"status_{pr_number}.json")

    cr_passed, approvers = check_reviews(reviews, row["author"], merged_at)
    checks_passed, problems = check_status_checks(collect_checks(check_runs, status), required, merged_at)

    row["CR_Passed"] = cr_passed
    row["CHECKS_PASSED"] = checks_passed
    row["approvers"] = ", ".join(approvers)
    row["check_problems"] = "; ".join(problems)
    return row


def run_transform():
    raw_folder = Path("data/raw")
    processed_folder = Path("data/processed")

    merged_prs = load_json(raw_folder / "merged_prs.json")
    required = load_json(raw_folder / "required_checks.json")
    failed_prs = load_json(raw_folder / "failed_prs.json")

    rows = [build_row(pr, required, failed_prs, raw_folder) for pr in merged_prs]

    processed_folder.mkdir(parents=True, exist_ok=True)
    file_path_report = processed_folder / "report.csv"

    with open(file_path_report, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    save_json(rows, processed_folder / "report.json")

    cr_count = sum(1 for row in rows if row["CR_Passed"] is True)
    checks_count = sum(1 for row in rows if row["CHECKS_PASSED"] is True)
    print(f"Report saved to {file_path_report}: {len(rows)} PRs, {cr_count} passed code review, {checks_count} passed checks")


if __name__ == "__main__":
    run_transform()