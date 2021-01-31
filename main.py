import yaml
import time

import requests
from bs4 import BeautifulSoup
from lxml import etree
from requests_oauthlib import OAuth1


with open('config.yml') as f:
    CONFIG = yaml.load(f, Loader=yaml.SafeLoader)


def tweet(source, section, title, link):
    if CONFIG['keys']['twitter']['enabled']:
        oauth = OAuth1(
            CONFIG['keys']['twitter']['consumer_key'],
            CONFIG['keys']['twitter']['consumer_secret'],
            CONFIG['keys']['twitter']['access_token'],
            CONFIG['keys']['twitter']['access_secret'],
        )
        
        message = f'{title}: {link} '
        if source:
            message += f'#{source} '
        message += f'#{section} #SGLiveNews'

        r = requests.post(
            'https://api.twitter.com/1.1/statuses/update.json',
            params={
                'status': message
            },
            headers={
                'User-Agent': 'fourjr/rss-feed-bot'
            },
            auth=oauth
        )

        if r.status_code != 200:
            print(f'Error posting {link} to twitter: {r.text}')


def telegram(source, section, title, link):
    if CONFIG['keys']['telegram']['enabled']:
        site = requests.get(link, headers={'User-Agent': 'fourjr/rss-feed-bot'})
        soup = BeautifulSoup(site.content, 'lxml')
        image_data = soup.find('meta', property='og:image')

        is_premium = soup.find('div', {'class': 'premium-read-more'})
        if is_premium:
            title = '[Premium] ' + title

        if image_data:
            image = image_data['content']
        else:
            image = None

        if source:
            message = f'#{source} '
        else:
            message = ''

        message += f'#{section} {title}'

        if image in CONFIG['config'].get('block_images', []):
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
            endpoint = 'Message'
        else:
            data['photo'] = image
            data['caption'] = message
            endpoint = 'Photo'

        r = requests.post(
            f'https://api.telegram.org/bot{CONFIG["keys"]["telegram"]["bot_token"]}/send{endpoint}',
            json=data
        )
        if r.status_code == 429:
            try:
                retry_after = r.json()['parameters']['retry_after']
            except KeyError:
                pass
            else:
                time.sleep(retry_after)
                return telegram(source, section, title, link)  # retry

        if r.status_code != 200:
            print(f'Error posting {link} to telegram: {r.status_code} - {r.text}')


try:
    with open('save.tmp') as f:
        completed = set(f.read().splitlines())
except FileNotFoundError:
    completed = set()

print('Started')

while True:
    for feed in CONFIG['feeds']:
        for category in feed['categories']:
            if isinstance(category, dict):
                feed_id = category['id']
                name = category['name']
            else:
                feed_id = str(category)
                name = str(category)

            req = requests.get(
                feed['root'].format(feed=feed_id),
                headers={'User-Agent': 'fourjr/rss-feed-bot'}
            )
            root = etree.fromstring(req.text.encode())
            articles = root.find('channel').findall('item')

            for i in articles:
                title = i.findtext('title').strip()
                if not feed.get('word_filter') or feed['word_filter'].lower() in title.lower():
                    link = i.findtext('link').strip()
                    if link not in completed:
                        tweet(feed.get('source'), name, title, link)
                        telegram(feed.get('source'), name, title, link)
                        completed.add(link)
                        print(f'Posted {title}')
                        with open('save.tmp', 'w+') as f:
                            f.write('\n'.join(completed))

        time.sleep(1)
