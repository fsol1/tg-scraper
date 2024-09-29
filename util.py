import csv
import datetime
import os
import re

import requests
from dotenv import load_dotenv
from termcolor import colored

load_dotenv()

test_channel = int(os.getenv("TEST_CHANNEL"))
ban_words = os.getenv("BAN_WORDS").split(",")

ids_to_names = {
    test_channel: "test_channel",
    # Add other channels as needed
    # -1001819368123 : "channel to listen",
}

ids = list(ids_to_names.keys())

# Regular expressions for address patterns
eth_address_pattern = re.compile(r"^(0x|0X)[0-9a-fA-F]{40}$")
sol_address_pattern = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")


def remove_stars(str):
    return str.replace("*", " ")


def contains_ban_word(str):
    text = str.lower()
    for word in ban_words:
        if word in text:
            return True
    return False


def get_address(str):
    if eth_address_pattern.match(str):
        return None
    match = sol_address_pattern.search(str)
    return match.group(0) if match else None


# Fetches token information from the Dexscreener API
def get_token_info(search_query):
    url = "https://api.dexscreener.com/latest/dex/search"
    parameters = {"q": search_query}

    try:
        response = requests.get(url, params=parameters)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


# Filters out unwanted tokens
def check_token_info(data):
    # Put your logic here (ex: don't buy tokens with low volume)
    return True


# Gets the token address from the token data
def get_token_address(data):
    return data["pairs"][0]["baseToken"]["address"]


# Strips messages and filters them for valid token addresses
def parse_message(message):
    # Check if the message is a reply or a forwarded message
    # They are often duplicates from previous messages
    if message.reply_to_message_id or message.forward_from_message_id:
        return None

    text = ""
    if message.text:
        text = message.text
    elif message.caption:
        # If the message contains an image, the text is in the caption attribute
        text = message.caption
    else:
        return None

    # Removing stars and newline so they don't interfer with the address parsing
    text = remove_stars(text)
    text = text.replace("\n", " ")

    # Filter out messages containing banned words
    if contains_ban_word(text):
        return None

    # Get address from message if there is one
    address = get_address(text)
    return address


# Gets SOL balance from the client for a public key
def get_balance(client, pubkey):
    return client.get_balance(pubkey).value


# Converts lamports to SOL
def lamports_to_sol(lamports):
    sol = lamports / 1e9  # 1 SOL = 1 billion lamports
    return sol


def format_datetime(input_datetime):
    formatted_datetime = input_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
    return formatted_datetime


def color_log(log, color, timestamp=True):
    ts = ""
    if timestamp:
        ts = format_datetime(datetime.datetime.now())
    formatted_message = ts + " " + log
    return colored(formatted_message, color)


def bold(log):
    return colored(log, attrs=["bold"])


def profit_log(profit):
    if profit > 0:
        return color_log("Profit: " + bold(str(profit) + " SOL"), "green")
    return color_log("Profit: " + bold(str(profit) + " SOL"), "red")


def add_line_to_csv(data, file_path="logs.csv"):
    with open(file_path, "a", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(data)


def f_datetime(dt):
    return dt.strftime("%Y-%m-%d_%H:%M:%S")


def calculate_pair_age(pair_timestamp, date):
    datetime_from_unix = datetime.datetime.utcfromtimestamp(
        pair_timestamp / 1000)
    current_datetime = date
    return current_datetime - datetime_from_unix


def add_data(data, date, caller, address, difference, info):
    data["date"] = date
    data["caller"] = caller
    data["address"] = address
    data["difference"] = difference
    data["info"] = info


# Adds log trade to the csv file
def add_line(data):
    line = [
        data["date"],
        data["caller"],
        data["address"],
        data["difference"],
        data["info"]["pairs"][0]["fdv"],
        data["profit"],
        data["info"]["pairs"][0]["liquidity"]["usd"],
        calculate_pair_age(data["info"]["pairs"][0]
                           ["pairCreatedAt"], data["date"]),
        data["info"]["pairs"][0]["priceChange"]["m5"],
        data["info"]["pairs"][0]["priceChange"]["h1"],
        data["info"]["pairs"][0]["priceChange"]["h6"],
        data["info"]["pairs"][0]["priceChange"]["h24"],
        data["info"]["pairs"][0]["volume"]["m5"],
        data["info"]["pairs"][0]["volume"]["h1"],
        data["info"]["pairs"][0]["volume"]["h6"],
        data["info"]["pairs"][0]["volume"]["h24"],
        data["info"]["pairs"][0]["txns"]["m5"]["buys"],
        data["info"]["pairs"][0]["txns"]["m5"]["sells"],
        data["info"]["pairs"][0]["txns"]["h1"]["buys"],
        data["info"]["pairs"][0]["txns"]["h1"]["sells"],
        data["info"]["pairs"][0]["txns"]["h6"]["buys"],
        data["info"]["pairs"][0]["txns"]["h6"]["sells"],
        data["info"]["pairs"][0]["txns"]["h24"]["buys"],
        data["info"]["pairs"][0]["txns"]["h24"]["sells"],
    ]
    add_line_to_csv(line)


# Gets SOL balance from a BonkBot message
def parse_balance(text):
    balance_pattern = re.compile(r"Balance: (\d+\.\d+) SOL")
    match = balance_pattern.search(text)
    if match:
        balance = match.group(1)
        balance_float = float(balance)
        return balance_float
    else:
        return None
