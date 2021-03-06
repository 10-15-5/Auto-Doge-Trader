import twitter
import configparser
import logging
import os
import sys
import requests

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.enums import *

from datetime import datetime

from twitter import TwitterError

from dateutil import parser

# ------------------------------------------------------------------
#   Logging Setup
# ------------------------------------------------------------------

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler("settings\\logs.log", encoding='utf8')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# ------------------------------------------------------------------

config = configparser.RawConfigParser()
configFilePath = r"settings/config.txt"
config.read(configFilePath, encoding="utf-8")

twitter_api = twitter.Api(consumer_key=config.get("CONFIG", "TWITTER_CONSUMER_KEY"),
                          consumer_secret=config.get("CONFIG", "TWITTER_CONSUMER_SECRET"),
                          access_token_key=config.get("CONFIG", "TWITTER_ACCESS_TOKEN_KEY"),
                          access_token_secret=config.get("CONFIG", "TWITTER_ACCESS_TOKEN_SECRET")
                          )

binance_client = Client(config.get("CONFIG", "BINANCE_PUBLIC_KEY"),
                        config.get("CONFIG", "BINANCE_PRIVATE_KEY")
                        )


def first_time():
    print("Please enter the username of people you want to watch (if checking multiple, "
          "seperate them with commas and do not include @):")
    handles = input()
    handles = handles.replace(" ", "").split(",")
    for i in range(len(handles)):
        try:
            # Check to see if it is a valid username and tweets aren't protected
            twitter_api.GetUserTimeline(screen_name=handles[i], count=1)
        except TwitterError as e:
            if str(e) == "Not authorized.":
                print("Sorry " + handles[i] + " has a protected account so we can't view their tweets, "
                                              "please try again")
            else:
                print("Sorry " + handles[i] + " doesn't exist, please try again")
            sys.exit()

    with open("settings/handles.txt", "w") as file:
        for i in range(len(handles)):
            if handles[i] == handles[-1]:
                value_to_write = handles[i]
            else:
                value_to_write = handles[i] + "\n"
            file.write(value_to_write)
    print("Thank you! Your usernames have been saved.")


def check_tweets_for_doge(twitter_handle):
    try:
        # Make sure the accounts haven't gone private lately
        statuses = twitter_api.GetUserTimeline(screen_name=twitter_handle, count=30)
    except TwitterError as e:
        if str(e) == "Not authorized.":
            logger.error(twitter_handle + " - Now a protected account so we can't view their tweets, "
                                          "please go to settings/handles.txt and remove "
                                          "their username for future runs")
        else:
            logger.error(twitter_handle + " - Account doesn't exist anymore,please remove "
                                          "them from settings/handles.txt")
        sys.exit()
    doge_mentioned = False

    for s in statuses:
        """
        Getting the tweets of each user, and cheking all their tweets in the last half hour to see if the contain the 
        word doge.
        """

        temp = parser.parse(s.created_at)  # Twitter API holds dates in a strnage foramt so have to parse them
        then = str(temp).split("+")[0]  # Just ignoring the microseconds as we don't need to be that precise
        created_at = parser.parse(then)  # Changeing the date back to dateformat so we can get the difference

        temp = datetime.now()
        now = str(temp).split(".")[0]
        nowtime = parser.parse(now)

        diff = nowtime - created_at
        if diff.days == 0 and (diff.seconds / 60) < 30:  # Checking all the tweets in the last half hour
            if "doge" in s.text.lower():
                logger.info(f'{"YES - "}{"Doge mentioned by "}{twitter_handle}{" on "}{s.created_at}')
                doge_mentioned = True

    if not doge_mentioned:
        logger.info(f'{"NO - "}{"Doge has not been mentioned by "}{twitter_handle}{" in the last half an hour."}')

    return doge_mentioned


def buy_doge():
    """doge_price = binance_client.get_symbol_ticker(symbol="DOGEEUR")
    doge_amount = int(config.get("CONFIG", "SPEND")) / float(doge_price["price"])
    print(round(doge_amount, 4))
    print(round(doge_amount, 4) * float(doge_price["price"]))"""
    try:
        binance_client.create_test_order(
            symbol='DOGEEUR',
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=1000)
    except BinanceAPIException as e:
        print(e.status_code)
        print(e.message)
    except BinanceOrderException as e:
        print(e)


def main():
    """if not os.path.isfile("settings/handles.txt"):
        first_time()

    with open("settings/handles.txt", "r") as file:
        handles = file.read().splitlines()
    for i in range(len(handles)):
        doge_mentioned = check_tweets_for_doge(handles[i])

    if doge_mentioned:
        buy_doge()"""

    buy_doge()


if __name__ == '__main__':
    main()
