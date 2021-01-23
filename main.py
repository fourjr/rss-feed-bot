import json
import os
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from lxml import etree
from requests_oauthlib import OAuth1

load_dotenv()

oauth = OAuth1(
    os.environ['CONSUMER_KEY'],
    os.environ['CONSUMER_SECRET'],
    os.environ['ACCESS_TOKEN'],
    os.environ['ACCESS_SECRET'],
)

dev_mode = bool(os.getenv('DEV_MODE', False))
chat_id = '@sglivenews' if not dev_mode else -1001430134386

def tweet(section, title, link):
    message = f'{title}: {link} #{section} #SGLiveNews'
    requests.post(
        'https://api.twitter.com/1.1/statuses/update.json',
        params={
            'status': message
        },
        headers={
            'User-Agent': 'SGLiveNews'
        },
        auth=oauth
    )

def telegram(section, title, link):
    site = requests.get(link, headers={'User-Agent': 'X'})
    soup = BeautifulSoup(site.content, 'lxml')
    image_data = soup.find('meta', property='og:image')
    if image_data:
        image = image_data['content']
    else:
        image = None

    message = f'#{section} {title}'

    if image == 'https://www.straitstimes.com/sites/all/themes/custom/bootdemo/images/facebook_default_pic_new.jpg':
        image = None

    if image is None:
        requests.post(
            f'https://api.telegram.org/bot{os.environ["TELEGRAM_BOT_TOKEN"]}/sendMessage',
            json={
                'chat_id': chat_id,
                'text': message,
                'reply_markup': {
                    'inline_keyboard': [
                        [{
                            'text': 'Read More',
                            'url': link
                        }]
                    ]
                }
            }
        )
    else:
        requests.post(
            f'https://api.telegram.org/bot{os.environ["TELEGRAM_BOT_TOKEN"]}/sendPhoto',
            json={
                'chat_id': chat_id,
                'photo': image,
                'caption': message,
                'reply_markup': {
                    'inline_keyboard': [
                        [{
                            'text': 'Read More',
                            'url': link
                        }]
                    ]
                }
            }
        )

BASE = 'https://www.straitstimes.com/news/{feed}/rss.xml'
QUERY = [
    'singapore',
    'asia',
    'tech',
    'world',
    'opinion'
]

completed = set()

try:
    with open('save.tmp') as f:
        completed |= set(f.readlines())
except FileNotFoundError:
    pass

print('Started')

while True:
    for category in QUERY:
        req = requests.get(
            BASE.format(feed=category),
            headers={'User-Agent': 'SGLiveNews'}
        )
        root = etree.fromstring(req.text.encode())
        articles = root.find('channel').findall('item')

        if articles:
            title = articles[0].findtext('title')
            description = articles[0].findtext('description')
            link = articles[0].findtext('link')
            if link not in completed:
                tweet(category, title, link)
                telegram(category, title, link)
                completed.add(link)
                print(f'Posted {title}')
                with open('save.tmp', 'w+') as f:
                    f.write('\n'.join(completed))

    time.sleep(3)
