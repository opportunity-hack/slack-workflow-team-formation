import os
from github import Github
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ.get("GITHUB_TOKEN")
slack_channel = "#something"

# Search for a user given a specific name - must be exact
def search_user(github_username):
    g = Github(TOKEN)
    try:
        user = g.get_user(login=github_username)
        return user.email
    except Exception as e:
        print(e)
        return None



# Create the next GitHub repo in the list - keep adding 1 to the oldest repo we have
def create_repo(slack_channel, github_username):
        g = Github(TOKEN)
        organization = g.get_organization("2021-opportunity-hack")
        repositories = organization.get_repos(sort="created", direction="asc")

        if repositories.totalCount != 0:
                repos = []
                for repo in repositories:
                        print(f"Found repo: {repo}")
                        repos.append(repo.name)

                last_repo = repos[-1]
                last_repo_number = last_repo.split("-")[1]
                print(f"Got last repo: {last_repo_number}")
                next_number = int(last_repo_number) + 1
                next_repo = f"Team-{next_number}"
        else:
                next_repo = "Team-1"


        print(f"Creating Repository for Team: {next_repo}")

        try:
            repository = organization.create_repo(
                f"{next_repo}",
                allow_rebase_merge=True,
                auto_init=False,
                description=f"#{slack_channel}",
                has_issues=True,
                has_projects=False,
                has_wiki=True,
                private=False,
                license_template="mit"
            )
            admins = ["bmysoreshankar", "jotpowers", "nemathew", "pkakathkar", "vertex", "gregv", github_username]

            for a in admins:
                repository.add_to_collaborators(a, permission="admin")
            readme_string = f'''
# Opportunity Hack 2021
👉 www.ohack.org/hackathon
## {next_repo}
- Slack channel: #{slack_channel}
- DevPost Project: `<add this later after you've created a submission>`

_All of the content below can be replaced whenever you're ready!_ 🙌

# Checklist
- ✅ Ensure you have your team added in a DevPost submission in [our DevPost for Opportunity Hack 2021](https://opportunity-hack-2021.devpost.com/)
- ✅ Be sure that you've read the [judging criteria](https://opportunity-hack-2021.devpost.com/#judging-criteria)
- ✅ Your DevPost final submission should include a demo video that is no longer than 4 minutes

# What should your final Readme look like?
Examples of stellar readmes:
- ✨ [2019 Team 3](https://github.com/2019-Arizona-Opportunity-Hack/Team-3)
- ✨ [2019 Team 6](https://github.com/2019-Arizona-Opportunity-Hack/Team-6)
- ✨ [2020 Team 2](https://github.com/2020-opportunity-hack/Team-02)
- ✨ [2020 Team 4](https://github.com/2020-opportunity-hack/Team-04)
- ✨ [2020 Team 8](https://github.com/2020-opportunity-hack/Team-08)
- ✨ [2020 Team 12](https://github.com/2020-opportunity-hack/Team-12)
'''

            repository.create_file("README.md", "Adding Readme!", readme_string)
            return repository
        except Exception as e:
            print(f"ERROR: Could not create repo for {next_repo}")
            print("Error:", e)

#Test
#search_user("gregvdasd")
