import sys
from linebot.models import *
import configparser
from linebot import LineBotApi
from linebot.exceptions import *
config = configparser.ConfigParser()
config.read('config.ini')
channelAccessToken = config['Shop']['channelAccessToken']
channelSecret = config['Shop']['channelSecret'] 


class line_bot_api(LineBotApi ):
    def push_message(self, *param):
        line_bot_api.push_message(param)

line_bot_api = LineBotApi(channelAccessToken)

line_bot_api.push_message("123", TextSendMessage(text="message"))
