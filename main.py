from extract import run_extract
from transform import run_transform
import argparse


def main():
    parser = argparse.ArgumentParser(description="Check if merged PRs in home-assistant/frontend passed code review and required checks")
    parser.add_argument("--limit", type=int, default=50, help="how many of the most recent merged PRs to check")
    parser.add_argument("--skip-extract", action="store_true", help="use the data already in data/raw instead of calling GitHub")
    args = parser.parse_args()

    if not args.skip_extract:
        run_extract(args.limit)
    run_transform()


if __name__ == "__main__":
    main()