import yaml
import time

import requests
from bs4 import BeautifulSoup
from lxml import etree
from requests_oauthlib import OAuth1


with open('config.yml') as f:
    CONFIG = yaml.load(f, Loader=yaml.BaseLoader)


def tweet(section, title, link):
    if CONFIG['keys']['twitter']['enabled']:
        oauth = OAuth1(
            CONFIG['keys']['twitter']['consumer_key'],
            CONFIG['keys']['twitter']['consumer_secret'],
            CONFIG['keys']['twitter']['access_token'],
            CONFIG['keys']['twitter']['access_secret'],
        )

        message = f'{title}: {link} #{section} #SGLiveNews'
        requests.post(
            'https://api.twitter.com/1.1/statuses/update.json',
            params={
                'status': message
            },
            headers={
                'User-Agent': 'fourjr/rss-feed-bot'
            },
            auth=oauth
        )


def telegram(section, title, link):
    if CONFIG['keys']['telegram']['enabled']:
        site = requests.get(link, headers={'User-Agent': 'fourjr/rss-feed-bot'})
        soup = BeautifulSoup(site.content, 'lxml')
        image_data = soup.find('meta', property='og:image')
        if image_data:
            image = image_data['content']
        else:
            image = None

        message = f'#{section} {title}'

        if image == 'https://www.straitstimes.com/sites/all/themes/custom/bootdemo/images/facebook_default_pic_new.jpg':
            image = None

        data = {
            'chat_id': CONFIG['keys']['telegram']['chat_id'],
            'reply_markup': {
                'inline_keyboard': [
                    [{
                        'text': 'Read More',
                        'url': link
                    }]
                ]
            }
        }

        if image is None:
            data['text'] = message
        else:
            data['photo'] = image
            data['caption'] = message

        requests.post(
            f'https://api.telegram.org/bot{CONFIG["keys"]["telegram"]["bot_token"]}/sendPhoto',
            json=data
        )


try:
    with open('save.tmp') as f:
        completed = set(f.read().splitlines())
except FileNotFoundError:
    completed = set()

print('Started')

while True:
    for feed in CONFIG['feeds']:
        for category in feed['categories']:
            req = requests.get(
                feed['root'].format(feed=category),
                headers={'User-Agent': 'fourjr/rss-feed-bot'}
            )
            root = etree.fromstring(req.text.encode())
            articles = root.find('channel').findall('item')

            for i in articles:
                title = i.findtext('title')
                link = i.findtext('link')
                if link not in completed:
                    tweet(category, title, link)
                    telegram(category, title, link)
                    completed.add(link)
                    print(f'Posted {title}')
                    with open('save.tmp', 'w+') as f:
                        f.write('\n'.join(completed))

        time.sleep(1)
