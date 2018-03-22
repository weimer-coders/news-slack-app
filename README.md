# Slack News
## [Working Title]

Slack News is a Slack bot that finds news for you and makes it easy to share with the rest of your channel. It uses the [News API](https://newsapi.org/) to find breaking stories from 134 of the top news sources across the globe. If it can't find what you're looking for, it'll even search News API's more than 30,000 other sources ranging from smaller news organizations to blogs.

## How Does It Work?

Once installed on your Slack team, Slack News can be called by using the `/news` Slash command in any channel or private group. You can provide it with any search term as if you were searching Google. It will then finds the top five stories matching your search and send them to you in private messages only you can see. Once you find the one you want, you can share it in the channel you're in, or dismiss it with the others.

On a more technical level, this app uses the [Flask](http://flask.pocoo.org/) framework and [Gunicorn](http://gunicorn.org/) server to process incoming webhooks from Slack's [slash commands](https://api.slack.com/slash-commands) and [interactive messages](https://api.slack.com/interactive-messages). Once the `/news` slash command is used, Slack sends a request to our server. It processes the input text and passes it to the [News API's top headlines](https://newsapi.org/docs/endpoints/top-headlines). If there are no results, it uses the [News API's everything endpoint](https://newsapi.org/docs/endpoints/everything) to find some online content that could potentially match the search.

Once the articles are found, Slack News creates the messages and responds with them [ephemerally](https://api.slack.com/methods/chat.postEphemeral) (which means they are temporary and only visible to one user). Along with the information on the articles are separate buttons to either dismiss the messages or share them publicly with the rest of the channel or group. Once a button is pressed, the app's interactive messages webhook handles the request and acts accordingly.

## Development

In order to download a run a copy of this server use the following instructions:

Create a virtualenv to store the codebase.
```bash
$ virtualenv news_slack_app
```

Activate the virtualenv.
```bash
$ cd news_slack_app
$ . bin/activate
```

Clone the git repository from GitHub.
```bash
$ git clone https://github.com/weimer-coders/news-slack-app.git news_slack_app
```

Enter the repo and install its dependencies.
```bash
$ cd news_slack_app
$ pip install -r requirements.txt
```

Make a copy of the .env file to add your own credentials
```bash
$ cp .env.template .env
```

Fill in your [Slack App](https://api.slack.com/apps) and [News API](https://newsapi.org/) credentials in the copied [env](.env.template#L2-L5) file.

Now run the test server with `manage.py` (which will load the environment variables for you) and check out the results on [localhost:5000/](localhost:5000).
```bash
$ python manage.py
```
