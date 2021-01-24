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

        message = f'{title}: {link} #{source} #{section} #SGLiveNews'
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

        message = f'#{source} #{section} {title}'

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

        r = requests.post(
            f'https://api.telegram.org/bot{CONFIG["keys"]["telegram"]["bot_token"]}/sendPhoto',
            json=data
        )
        if r.status_code != 200:
            print(f'Error posting {link} to telegram: {r.text}')


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
                id = category['id']
                name = category['name']
            else:
                id = str(category)
                name = str(category)

            req = requests.get(
                feed['root'].format(feed=id),
                headers={'User-Agent': 'fourjr/rss-feed-bot'}
            )
            root = etree.fromstring(req.text.encode())
            articles = root.find('channel').findall('item')

            for i in articles:
                title = i.findtext('title').strip()
                if not feed.get('word_filter') or feed['word_filter'] in title:
                    link = i.findtext('link').strip()
                    if link not in completed:
                        tweet(feed['source'], name, title, link)
                        telegram(feed['source'], name, title, link)
                        completed.add(link)
                        print(f'Posted {title}')
                        with open('save.tmp', 'w+') as f:
                            f.write('\n'.join(completed))

        time.sleep(1)
