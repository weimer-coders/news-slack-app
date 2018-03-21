from flask import Flask, request, jsonify
from newsapi import NewsApiClient
from slackclient import SlackClient
from threading import Thread
import json
import os

news_api_token = os.environ.get('news_api_token')
slack_bot_token = os.environ.get('slack_bot_token')
slack_verification_token = os.environ.get('slack_verification_token')

newsapi = NewsApiClient(api_key=news_api_token)
sc = SlackClient(slack_bot_token)
app = Flask(__name__)


def get_the_news(payload):
    user_id = payload['user_id']
    channel_id = payload['channel_id']

    search_term = payload['text']
    all_headlines = newsapi.get_top_headlines(q=search_term)
    top_headlines = all_headlines['articles'][:5]

    messages = create_interactive_messages(top_headlines)
    for message in messages:
        sc.api_call(
            "chat.postEphemeral",
            channel=channel_id,
            attachments=message,
            user=user_id
        )


def create_interactive_messages(headlines):
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
                        "value": json.dumps(headline),
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
    return [
        {
            "title": headline["title"],
            "author_name": headline["source"]["name"],
            "text": headline["description"],
            "title_link": headline["url"],
            "thumb_url": headline["urlToImage"],
        }
    ]


@app.route('/', methods=['GET'])
def index():
    """
    Confirm that the server is working.
    """
    return ('This web app is working!')


@app.route('/slack-slash', methods=['POST'])
def slack_slash():
    if request.form["token"] != slack_verification_token:
        return (None, 403, None)

    thr = Thread(target=get_the_news, args=[request.form])
    thr.start()

    return ('', 204)


@app.route('/slack-button', methods=['POST'])
def slack_button():
    payload = json.loads(request.form['payload'])
    if payload["token"] != slack_verification_token:
        return (None, 403, None)

    if payload["actions"][0]["name"] == "share":
        headline = json.loads(payload["actions"][0]["value"])
        message = create_story_message(headline)

        channel_id = payload["channel"]["id"]
        user_id = payload["user"]["id"]

        sc.api_call(
            "chat.postMessage",
            text="<@%s> shared this:" % user_id,
            channel=channel_id,
            attachments=message,
        )

    return jsonify({
        'delete_original': True
    })


@app.after_request
def call_after_request_callbacks(response):
    print 'This is after the request!!'
    return response


if __name__ == '__main__':
    # Fire up the Flask test server
    app.run(debug=True, use_reloader=True)
