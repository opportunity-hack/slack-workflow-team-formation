import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
load_dotenv()

from slack_bolt.workflows.step import WorkflowStep
from github_repo_actions import create_repo, search_user
from flask import Flask, redirect, url_for, render_template, request, session


import logging

# logger in a global context
# requires importing logging
logging.basicConfig(level=logging.DEBUG)

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("WORKFLOW_BOT_TOKEN"))

flaskapp = Flask(__name__)
flaskapp.secret_key = os.urandom(12)  # Generic key for dev purposes only

from colorutils import Color



# Heroku
from flask_heroku import Heroku
heroku = Heroku(flaskapp)

def save(ack, view, update):
    ack()

    values = view["state"]["values"]
    print(f"Values: {values}")
    github_username = values["github_username_input"]["github_username"]
    slack_channel = values["slack_channel_input"]["slack_channel"]
    slack_username = values["slack_username_input"]["slack_username"]
    github_repo = values["github_repo_output"]["github_repo"]

    inputs = {
        "github_username": {"value": github_username["value"]},
        "slack_channel": {"value": slack_channel["value"]},
        "slack_username": {"value": slack_username["value"]},
        "github_repo": {"value": github_repo["value"]}
    }
    outputs = [
        {
            "type": "text",
            "name": "github_username",
            "label": "GitHub Username",
        },
        {
            "type": "text",
            "name": "slack_channel",
            "label": "Slack channel",
        },
        {
            "type": "text",
            "name": "slack_username",
            "label": "Slack username",
        },
        {
            "type": "text",
            "name": "github_repo",
            "label": "Github Repo",
        }
    ]
    update(inputs=inputs, outputs=outputs)


def edit(ack, step, configure):
    ack()

    print(step)

    github_username = step["inputs"]["github_username"]["value"] if "github_username" in step["inputs"] else ""
    slack_username = step["inputs"]["slack_username"]["value"] if "slack_username" in step["inputs"] else ""
    slack_channel = step["inputs"]["slack_channel"]["value"] if "slack_channel" in step["inputs"] else ""
    github_repo = step["inputs"]["github_repo"]["value"] if "github_repo" in step["inputs"] else ""

    # This helped to figure out the inital value part
    # https://api.slack.com/tutorials/workflow-builder-steps-pt-2
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":wave: We use this Step to obtain GitHub and team information from each person"
            }
        },
        {
            "type": "input",
            "block_id": "github_username_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "github_username",
                "placeholder": {
                    "type": "plain_text",
                    "text": "GitHub username of person",
                    "emoji": False
                },
                "initial_value": github_username
            },
            "label": {
                "type": "plain_text",
                "text": "What is the GitHub username?"
            }
        },
        {
            "type": "input",
            "block_id": "slack_username_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "slack_username",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Slack username of submitter"
                },
                "initial_value": slack_username
            },
            "label": {
                "type": "plain_text",
                "text": "Slack username of submitter?"
            }
        },
        {
            "type": "input",
            "block_id": "slack_channel_input",
            "element": {
                "type": "plain_text_input",
                "action_id": "slack_channel",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Public Slack channel"
                },
                "initial_value": slack_channel
            },
            "label": {
                "type": "plain_text",
                "text": "What is their public Slack channel?"
            }
        },
        {
            "type": "input",
            "block_id": "github_repo_output",
            "element": {
                "type": "plain_text_input",
                "action_id": "github_repo",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Generated GitHub Repo"
                },
                "initial_value": github_repo
            },
            "label": {
                "type": "plain_text",
                "text": "What GitHub Repo was automatically generated?"
            }
        }

    ]
    configure(blocks=blocks)


def execute(step, complete, fail, logger):
    print(f"Step: {step}")
    inputs = step["inputs"]
    print(f"Inputs: {inputs}")

    slack_username = inputs["slack_username"]["value"]
    slack_username_cleaned = slack_username.replace("<@", "").replace(">", "")
    print(f"Slack Username: {slack_username_cleaned}")

    github_username = inputs["github_username"]["value"]
    user_exists = search_user(github_username)
    if user_exists is None:
        error_message = f":sadparrot: Hey there, bad news, I could not find your GitHub username: `{github_username}` so we haven't created your team.\nPlease check your GitHub username and try again."
        app.client.chat_postMessage(channel=slack_username_cleaned, text=error_message)
        return

    slack_channel = inputs["slack_channel"]["value"]
    slack_channel_cleaned = slack_channel.replace("<#", "").replace(">", "")
    print(f"Channel: {slack_channel}")
    channel_response = app.client.conversations_info(channel=slack_channel_cleaned)
    channel_name = channel_response["channel"]["name"]
    print(f"Channel Name: {channel_response}")

    # if everything was successful
    repo_result = create_repo(channel_name, github_username)
    print(f"Repository Result: {repo_result}")

    if repo_result is None or repo_result.name is None:
        print("ERROR: Something went wrong with GitHub repo creation")
        return
    team_number = repo_result.name.split("-")[1]


    result = app.client.chat_postMessage(
        channel="C01BR06N03G",  # team-formation Slack channel
        text=f"Created Repository:\n Repo: {repo_result.name}\n GitHub Username: {github_username}\n Team Slack Channel: {slack_channel_cleaned}",
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":fiestaparrot: Created Repository\n:discoparrot: Repo: <https://github.com/2021-opportunity-hack/{repo_result.name}|{repo_result.name}> (Team Number: {team_number})\n:tacoparrot: GitHub Username for Admin: {github_username} / Slack User: {slack_username}\n:reversecongaparrot: Team Slack Channel: {slack_channel}\nYou will be added as an administrator on your team’s GitHub repository, check your email associated with your GitHub account as you will need to accept this request before you will have access. <https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-user-account/managing-access-to-your-personal-repositories/inviting-collaborators-to-a-personal-repository|Add your team to the repo using these instructions.> :partygopher: All code from the hackathon should be placed here."
            }
        }]
    )
    logger.info(result)

    result = app.client.chat_postMessage(
        channel=slack_channel_cleaned,  # The team's Slack channel
        text=f"Created Repository:\n Repo: {repo_result.name}\n GitHub Username: {github_username}\n Team Slack Channel: {slack_channel_cleaned}",
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":fiestaparrot: Created Repository\n:discoparrot: Repo: <https://github.com/2021-opportunity-hack/{repo_result.name}|{repo_result.name}> (Team Number: {team_number})\n:tacoparrot: GitHub Username for Admin: {github_username} / Slack User: {slack_username}\n:reversecongaparrot: Team Slack Channel: {slack_channel}\nYou will be added as an administrator on your team’s GitHub repository, check your email associated with your GitHub account as you will need to accept this request before you will have access. <https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-user-account/managing-access-to-your-personal-repositories/inviting-collaborators-to-a-personal-repository|Add your team to the repo using these instructions.> :partygopher: All code from the hackathon should be placed here."
            }
        }]
    )
    logger.info(result)

    outputs = {
        "github_username": github_username,
        "slack_channel": slack_channel,
        "team_number": team_number,
        "github_repo": f"https://github.com/2021-opportunity-hack/{repo_result.name}"
    }
    print(f"Outputs: {outputs}")

    complete(outputs=outputs)

    # if something went wrong
    # error = {"message": "Just testing step failure!"}
    # fail(error=error)


ws = WorkflowStep(
    callback_id="tutorial_example_step",
    edit=edit,
    save=save,
    execute=execute,
)
app.step(ws)

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["WORKFLOW_APP_TOKEN"]).start()
    app.run(debug=True, use_reloader=True, host="0.0.0.0")
