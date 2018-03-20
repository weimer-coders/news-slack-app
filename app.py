from flask import Flask, request
from newsapi import NewsApiClient
from slackclient import SlackClient
import json
import credentials

newsapi = NewsApiClient(api_key=credentials.news_api_token)
sc = SlackClient(credentials.slack_api_token)
app = Flask(__name__)


def create_messages(headlines):
    messages = []
    for headline in headlines:
        message = [
            {
                "title": headline["title"],
                "author_name": headline["source"]["name"],
                "text": headline["description"],
                "text_link": headline["url"],
                "thumb_url": headline["urlToImage"],
            },
            {
                "title": "Share in channel?",
                "callback_id": json.dumps(headline),
                "attachment_type": "default",
                "actions": [
                    {
                        "name": "share",
                        "text": "Share",
                        "type": "button",
                        "value": "share",
                        "style": "primary"
                    },
                    {
                        "name": "dismiss",
                        "text": "Dismiss",
                        "type": "button",
                        "value": "dismiss",
                        "style": "danger"
                    }
                ]
            }
        ]
        messages.append(message)

    return messages


@app.route('/', methods=['GET'])
def index():
    """
    Confirm that the server is working.
    """
    return ('This web app is working!')


@app.route('/slack-slash', methods=['POST'])
def slack_slash():
    if request.form["token"] != credentials.slack_verification_token:
        return (None, 403, None)

    user_id = request.form['user_id']
    channel_id = request.form['channel_id']

    search_term = request.form['text']
    all_headlines = newsapi.get_top_headlines(q=search_term)
    top_headlines = all_headlines['articles'][:3]

    messages = create_messages(top_headlines)
    for message in messages:
        sc.api_call(
            "chat.postEphemeral",
            channel=channel_id,
            attachments=message,
            user=user_id
        )

    return ('This web app is working!')


@app.route('/slack-button', methods=['POST'])
def slack_button():
    payload = json.loads(request.form['payload'])
    if payload["token"] != credentials.slack_verification_token:
        return (None, 403, None)

    print payload["callback_id"]
    return ('text')


if __name__ == '__main__':
    # Fire up the Flask test server
    app.run(debug=True, use_reloader=True)
