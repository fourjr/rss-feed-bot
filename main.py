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

    link = f'https://t.me/iv?url={link}&rhash=5e3df8a7095695'
    message = f'{title}: {link} #{section} #SGLiveNews'

    if image is None:
        requests.post(
            f'https://api.telegram.org/bot{os.environ["TELEGRAM_BOT_TOKEN"]}/sendMessage',
            json={
                'chat_id': '@sglivenews',
                'text': message,
            }
        )
    else:
        requests.post(
            f'https://api.telegram.org/bot{os.environ["TELEGRAM_BOT_TOKEN"]}/sendPhoto',
            json={
                'chat_id': '@sglivenews',
                'photo': image,
                'caption': message,
            }
        )

BASE = 'https://www.straitstimes.com/news/{feed}/rss.xml'
QUERY = {
    'singapore': [],
    'asia': [],
    'tech': [],
    'world': [],
    'opinion': []
}

try:
    with open('save.json') as f:
        QUERY.update(json.load(f))
except FileNotFoundError:
    pass

print('Started')

while True:
    for k, v in QUERY.items():
        req = requests.get(
            BASE.format(feed=k),
            headers={'User-Agent': 'SGLiveNews'}
        )
        root = etree.fromstring(req.text.encode())
        articles = root.find('channel').findall('item')

        if articles:
            title = articles[0].findtext('title')
            description = articles[0].findtext('description')
            link = articles[0].findtext('link')
            if link not in v:
                tweet(k, title, link)
                telegram(k, title, link)
                QUERY[k].append(link)
                print(f'Posted {title}')
                with open('save.json', 'w+') as f:
                    json.dump(QUERY, f)

    time.sleep(3)
