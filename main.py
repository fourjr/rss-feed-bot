import yaml
import time

import requests
from bs4 import BeautifulSoup
from lxml import etree
from requests_oauthlib import OAuth1


with open('config.yml') as f:
    CONFIG = yaml.load(f, Loader=yaml.BaseLoader)

oauth = OAuth1(
    CONFIG['keys']['twitter']['consumer_key'],
    CONFIG['keys']['twitter']['consumer_secret'],
    CONFIG['keys']['twitter']['access_token'],
    CONFIG['keys']['twitter']['access_secret'],
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


completed = set()

try:
    with open('save.tmp') as f:
        completed |= set(f.read().splitlines())
except FileNotFoundError:
    pass

print('Started')

while True:
    for feed in CONFIG['feeds']:
        for category in feed['categories']:
            req = requests.get(
                feed['root'].format(feed=category),
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
