from flask import Flask, request, jsonify
from newsapi import NewsApiClient
from slackclient import SlackClient
from threading import Thread
import json
import os

NEWS_API_TOKEN = os.environ.get('NEWS_API_TOKEN')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = os.environ.get('SLACK_APP_TOKEN')
SLACK_VERIFICATION_TOKEN = os.environ.get('SLACK_VERIFICATION_TOKEN')
BOT_USER_ID = os.environ.get('BOT_USER_ID')

newsapi = NewsApiClient(api_key=NEWS_API_TOKEN)
sc_bot = SlackClient(SLACK_BOT_TOKEN)
sc_app = SlackClient(SLACK_APP_TOKEN)

app = Flask(__name__)


def get_the_news(payload):
    """
    Uses the News API to get news stories based on a search query
    """
    user_id = payload['user_id']
    channel_id = payload['channel_id']

    # Make sure the bot is in the channel it's being called from
    sc_app.api_call(
        "conversations.invite",
        channel=channel_id,
        users=BOT_USER_ID
    )

    search_term = payload['text']

    all_headlines = newsapi.get_top_headlines(q=search_term)
    top_headlines = all_headlines['articles'][:5]

    # If there are top headlines, reply to the user
    if len(top_headlines) > 0:
        messages = create_interactive_messages(top_headlines)
        for message in messages:
            sc_bot.api_call(
                "chat.postEphemeral",
                channel=channel_id,
                attachments=message,
                user=user_id
            )
    # If there are not top headlines, try getting any headlines
    else:

        all_headlines = newsapi.get_everything(q=search_term, sort_by='relevancy')
        top_headlines = all_headlines['articles'][:5]

        # If there are any headlines, reply to the user
        if len(top_headlines) > 0:
            messages = create_interactive_messages(top_headlines)
            for message in messages:
                sc_bot.api_call(
                    "chat.postEphemeral",
                    channel=channel_id,
                    attachments=message,
                    user=user_id
                )
        # If there are no headlines, respond saying so
        else:
            sc_bot.api_call(
                "chat.postEphemeral",
                channel=channel_id,
                text="No news found with the search `%s`" % search_term,
                user=user_id
            )


def create_interactive_messages(headlines):
    """
    Creates attatchemtns for interactive messages with buttons to share and/or dismiss them.
    """
    messages = []
    for headline in headlines:
        message = [
            {
                "title": headline["title"],
                "author_name": headline["source"]["name"],
                "text": headline["description"],
                "title_link": headline["url"],
                "thumb_url": headline["urlToImage"],
            },
            {
                "title": "Share in channel?",
                "callback_id": "share",
                "attachment_type": "default",
                "actions": [
                    {
                        "name": "share",
                        "text": "Share",
                        "type": "button",
                        "value": json.dumps(headline),  # Used to recreate the message when pushed
                        "style": "primary"
                    },
                    {
                        "name": "dismiss",
                        "text": "Dismiss",
                        "type": "button",
                        "value": "",
                        "style": "danger"
                    }
                ]
            }
        ]
        messages.append(message)

    return messages


def create_story_message(headline):
    """
    Creates attatchement for headline being shared
    """
    return [
        {
            "title": headline["title"],
            "author_name": headline["source"]["name"],
            "text": headline["description"],
            "title_link": headline["url"],
            "thumb_url": headline["urlToImage"],
        }
    ]


def authorize(token):
    """
    Verfiy the message is coming from Slack
    """
    if token == SLACK_VERIFICATION_TOKEN:
        return True
    else:
        return False


@app.route('/', methods=['GET'])
def index():
    """
    Confirm that the server is working
    """
    return ('Working.')


@app.route('/slack-slash', methods=['POST'])
def slack_slash():
    """
    Handles slash command webhooks being sent to this server
    """
    if not authorize(request.form["token"]):
        return (None, 403, None)

    # Start getting and posting the news in a new thread
    thr = Thread(target=get_the_news, args=[request.form])
    thr.start()

    return ('', 204)


@app.route('/slack-button', methods=['POST'])
def slack_button():
    """
    Handles interactive message webhooks being sent to this server
    """
    payload = json.loads(request.form['payload'])
    if not authorize(payload["token"]):
        return (None, 403, None)

    # If the share button was pressed
    if payload["actions"][0]["name"] == "share":
        headline = json.loads(payload["actions"][0]["value"])
        message = create_story_message(headline)

        channel_id = payload["channel"]["id"]
        user_id = payload["user"]["id"]

        sc_bot.api_call(
            "chat.postMessage",
            text="<@%s> shared this:" % user_id,
            channel=channel_id,
            attachments=message,
        )

    # Regardless, delete the message
    return jsonify({
        'delete_original': True
    })


if __name__ == '__main__':
    # Fire up the Flask test server
    app.run(debug=True, use_reloader=True)
