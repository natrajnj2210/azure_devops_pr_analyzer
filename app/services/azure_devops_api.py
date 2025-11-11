import requests
import pandas as pd

class AzureDevopsAPI:
    """Handles authentication and REST calls to Azure DevOps."""

    def __init__(self, pat: str, org: str, proj: str, repo: str, pr_no: str):
        self.pat = pat
        self.org = org
        self.project = proj
        self.repo_name = repo
        self.pr_no = pr_no
        self.session = requests.Session()
        self.session.auth = ("", pat)
        self.session.headers.update({"Content-Type": "application/json"})

        # Get repository ID first
        self.repo_id = self._get_repo_id()

    def _get_repo_id(self):
        """Fetch the repo ID for given repo name."""
        url = f"https://dev.azure.com/{self.org}/{self.project}/_apis/git/repositories?api-version=7.1"
        resp = self.session.get(url)
        if resp.status_code != 200:
            raise Exception(f"❌ Failed to fetch repo list: {resp.text[:200]}")
        for repo in resp.json().get("value", []):
            if repo["name"].lower() == self.repo_name.lower():
                return repo["id"]
        raise Exception(f"❌ Repository '{self.repo_name}' not found in project '{self.project}'.")

    def get_commits(self):
        """Fetch commits for the PR using repo ID."""
        url = f"https://dev.azure.com/{self.org}/{self.project}/_apis/git/repositories/{self.repo_id}/pullRequests/{self.pr_no}/commits?api-version=7.1"
        resp = self.session.get(url)
        if resp.status_code != 200:
            raise Exception(f"❌ Failed to fetch commits: {resp.text[:200]}")
        return resp.json().get("value", [])

    def get_merging_files(self):
        """Fetch all files from all commits in the PR."""
        file_dict = {}

        for commit in self.get_commits():
            url = f"https://dev.azure.com/{self.org}/{self.project}/_apis/git/repositories/{self.repo_id}/commits/{commit['commitId']}/changes?api-version=7.1"
            resp = self.session.get(url)
            if resp.status_code != 200:
                raise Exception(f"❌ Failed to fetch commit changes: {resp.text[:200]}")

            for file in resp.json().get("changes", []):
                item = file.get("item", {})
                if item.get("gitObjectType") != "blob":
                    continue

                user = commit["author"]["name"]
                file_name = item["path"].split("/")[-1]
                edit_flag = 1 if file["changeType"].lower() == "edit" else 0
                add_flag = 1 if file["changeType"].lower() == "add" else 0

                if file_name not in file_dict:
                    file_dict[file_name] = {
                        "users": [user],
                        "edit_flag": edit_flag,
                        "add_flag": add_flag
                    }
                else:
                    if user not in file_dict[file_name]["users"]:
                        file_dict[file_name]["users"].append(user)
                    if edit_flag:
                        file_dict[file_name]["edit_flag"] = 1
                    if add_flag:
                        file_dict[file_name]["add_flag"] = 1

        return file_dict

    def close(self):
        self.session.close()


def fetch_pr_data(org, project, repo, pr_number, pat):
    """Wrapper for Streamlit app: returns DataFrame for PR changes."""
    api = AzureDevopsAPI(pat, org, project, repo, pr_number)
    file_data = api.get_merging_files()
    api.close()

    if not file_data:
        return pd.DataFrame()

    rows = []
    for i, (fname, info) in enumerate(file_data.items(), start=1):
        rows.append({
            "S.No": i,
            "File Name": fname,
            "Modified By": ", ".join(info["users"]),
            "Is_Modified": "TRUE" if info["edit_flag"] else "FALSE",
            "Is_Added_New": "TRUE" if info["add_flag"] else "FALSE"
        })

    return pd.DataFrame(rows)
