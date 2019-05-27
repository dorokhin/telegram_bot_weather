import os
import uuid
import logging
import requests
import telegram
import sentry_sdk
from telegram.error import NetworkError
from flask import Flask, request, jsonify
from sentry_sdk import capture_exception, capture_message, configure_scope


sentry_sdk.init("https://29bdbb904ec7432084ff4ac13fd7d584@sentry.io/1468408")

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
VK_ACCESS_TOKEN = os.environ.get('VK_ACCESS_TOKEN')

domain_name = os.environ.get('BOT_DOMAIN_NAME')
webhook_url = '/{0}'.format(uuid.uuid4())


app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)


def build_url(domain, url):
    return 'https://{0}/{1}'.format(domain, url)


def get_vk_user_info(vk_id, access_token):
    url = "https://api.vk.com/method/users.get?user_ids={0}&fields=&v=5.95&access_token={1}".format(vk_id, access_token)
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Content-Encoding': 'utf-8'}
    response = requests.get(url, headers=headers)
    return response.json()


logging.info('Webhook url is: {0}'.format(build_url(domain_name, webhook_url)))


def get_username_or_id(link_to_user_account):
    try:
        user_id = link_to_user_account.split('/id')[-1]
    except ValueError:
        user_id = link_to_user_account.split('/')[-1]
    return user_id


@app.route('/')
def index():
    logging.info('Someone visit bot\'s main page')
    return jsonify({'msg': 'success'})


@app.route(webhook_url, methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        chat_id = update.message.chat.id

        text = update.message.text.encode('utf-8')
        user_data = get_username_or_id(text)

        try:
            vk_user_id = get_vk_user_info(user_data, VK_ACCESS_TOKEN)['response'][0]['id']
            with configure_scope() as scope:
                scope.set_extra('vk_user_id', vk_user_id)
                scope.set_extra('chat_id', chat_id)

        except Exception:
            capture_message('get_vk_user_info failed')
            vk_user_id = None

        if vk_user_id.isdigit():
            bot.sendMessage(chat_id=chat_id, text=vk_user_id)
        else:
            bot.sendMessage(chat_id=chat_id, text="Can't get user id")
    return 'ok'


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    try:
        s = bot.setWebhook(build_url(domain_name, webhook_url))
        if s:
            return jsonify({'msg': 'webhook setup success'})
        else:
            return jsonify({'msg': 'webhook setup failed'})
    except NetworkError as e:
        capture_exception(e)
        return jsonify({'msg': 'webhook setup failed'})


if __name__ == '__main__':
    app.run()
