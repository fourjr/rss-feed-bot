# RSS Feed Bot

The script scrapes RSS feeds (every 1 second, rotational) and shares it to Telegram or Twitter. It is intended to be used for live news but should support other [similarly structured](https://www.w3schools.com/xml/xml_rss.asp) RSS feeds.

## Live Example
Telegram: [@SGLiveNews](https://t.me/sglivenews)

## Configuration
1. Save `config.yml.example` as `config.yml`.
2. Obtain twitter keys from [Twitter Developer API Dashboard](https://developer.twitter.com/en/portal/dashboard).
3. Obtain telegram keys from [Botfather](https://core.telegram.org/bots#creating-a-new-bot).
4. Create a telegram channel or group chat and [obtain the chat_id](https://2ngc6.csb.app/). If your telegram channel is public, setting the `chat_id` as `@linkname` will work as well.
5. Find an RSS Feed (e.g. [Straits Times Singapore](https://www.straitstimes.com/RSS-Feeds)).
6. Obtain root url (e.g. https://www.straitstimes.com/news/{feed}/rss.xml), {feed} is a template variable that will be filled in by the script.
7. Fill in the various categories that you wish to scrape.
8. You may include as many feeds as desired. The more feeds, the longer a cycle will take.

## Using the script
1. [Python 3.6+](https://www.python.org/downloads/) is required.
2. `pip install -r requirements.txt`
3. `python main.py`

## Known Limitations
- Twitter has a tendency to "ghostban" the account due to excessive link posting with similar message structure. Manual phone verification is needed every few hours.
- Support for [Telegram Instant View](https://instantview.telegram.org/) would be great.
