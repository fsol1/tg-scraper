import asyncio
import datetime
import os

import uvloop
from dotenv import load_dotenv
from pyrogram import Client as PyroClient
from pyrogram import filters
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey

from util import *

load_dotenv()

# Retrieve environment variables
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
test_channel = int(os.getenv("TEST_CHANNEL"))
holding_time = int(os.getenv("HOLDING_TIME"))
pubkey = Pubkey.from_string(os.getenv("PUBKEY"))

solana_client = SolanaClient("https://api.mainnet-beta.solana.com")

bonkbotmcqueen = 6823648642
last_buy_message_id = 0
data = {}
bot_switch = True

uvloop.install()
state_lock = asyncio.Lock()

app = PyroClient("my_account", api_id=api_id, api_hash=api_hash)

balance = lamports_to_sol(get_balance(solana_client, pubkey))
print(color_log("Launching bot...", "yellow"))
print(color_log("Starting balance: " + bold(str(balance) + " SOL"), "yellow"))


# Pauses the bot when receiving "pause" from test channel
@app.on_message(filters.chat(test_channel) & filters.regex("pause"))
async def pause_bot(client, message):
    global bot_switch
    async with state_lock:
        bot_switch = False
        print(color_log("Bot turned off", "yellow"))


# Unpauses the bot when receiving "unpause" from test channel
@app.on_message(filters.chat(test_channel) & filters.regex("unpause"))
async def unpause_bot(client, message):
    global bot_switch
    async with state_lock:
        bot_switch = True
        print(color_log("Bot turned on", "yellow"))


# Scraps messages coming from channels and triggers buy
@app.on_message(filters.chat(ids))
async def listen(client, message):
    global last_buy_message_id
    global bot_switch
    global data
    async with state_lock:

        # Log new message
        receive_timestamp = datetime.datetime.now()
        difference = (receive_timestamp - message.date).total_seconds()
        print(
            color_log(
                "New message from "
                + bold(ids_to_names[message.chat.id])
                + color_log(str(difference), "blue", False),
                "blue",
            )
        )

        # Parse message for address
        address = parse_message(message)
        if address:

            # Check if the token is good
            print(color_log("Address detected " + bold(address), "magenta"))
            info = get_token_info(address)
            check = check_token_info(info)
            if check:

                # Get the token address from the token information
                token_address = get_token_address(info)

                # Check if bot is on and there is no ongoing trade
                if last_buy_message_id == 0 and bot_switch:
                    print(color_log("Buy triggered", "cyan"))

                    # Change state to ongoing trade
                    last_buy_message_id = 1

                    # Send the token address to BonkBot for auto-buy
                    await app.send_message("mcqueen_bonkbot", token_address)
                    add_data(
                        data,
                        receive_timestamp,
                        ids_to_names[message.chat.id],
                        token_address,
                        difference,
                        info,
                    )


# Logs when BonkBot sends the buy transaction
@app.on_message(filters.chat(bonkbotmcqueen) & filters.regex("Initiating Auto Buy"))
async def initiating_buy(client, message):
    print(color_log("Initiating Auto Buy...", "cyan"))


# Gets the wallet message from BonkBot if there is an ongoing trade
@app.on_message(
    filters.chat(bonkbotmcqueen)
    & filters.regex("Welcome to BonkBot|Positions Overview:")
)
async def get_wallet_message(client, message):
    global last_buy_message_id
    async with state_lock:
        if last_buy_message_id != 0:
            await message.click("Wallet")


# Parses wallet balance from BonkBot and logs the trade in the csv file
@app.on_message(filters.chat(bonkbotmcqueen) & filters.regex("Your Wallet:"))
async def parse_balance_from_bot(client, message):
    global balance
    global data
    global last_buy_message_id
    async with state_lock:
        if last_buy_message_id != 0:
            new_balance = parse_balance(message.text)
            profit = round(new_balance - balance, 9)
            data["profit"] = profit
            print(profit_log(profit))
            add_line(data)
            balance = new_balance
            last_buy_message_id = 0


# Logs successful trade
@app.on_edited_message(filters.chat(bonkbotmcqueen) & filters.regex("Swap Successful"))
async def swap_succesful(client, message):
    global balance
    global data
    async with state_lock:
        if "Auto Buy" in message.text:
            print(color_log("Token bought", "cyan"))
        else:
            print(color_log("Token sold", "cyan"))
            # Get BonkBot's home message
            await app.send_message("mcqueen_bonkbot", "/home")


# Triggers sell after waiting for a given time (in seconds)
@app.on_message(filters.chat(bonkbotmcqueen) & filters.regex("Generate PnL Card"))
async def listen_bonkbot_buy(client, message):
    global last_buy_message_id
    async with state_lock:
        last_buy_message_id = message.id
        await asyncio.sleep(holding_time)
        await message.click("Sell 100%")
        print(color_log("Sell triggered", "cyan"))


# Logs when BonkBot sends the sell transaction
@app.on_message(filters.chat(bonkbotmcqueen) & filters.regex("Initiating sell"))
async def initaiting_sell(client, message):
    print(color_log("Initiating Sell...", "cyan"))


# Reinitialize state if the token is not found
@app.on_message(filters.chat(bonkbotmcqueen) & filters.regex("Token not found"))
async def listen_bonkbot_token_not_found(client, message):
    global last_buy_message_id
    async with state_lock:
        last_buy_message_id = 0
        print(color_log("Token not found", "cyan"))


# Pauses the bot when BonkBot is updating
@app.on_message(filters.chat(bonkbotmcqueen) & filters.regex("updating"))
async def listen_bonkbot_updating(client, message):
    global last_buy_message_id
    global bot_switch
    async with state_lock:
        bot_switch = False
        last_buy_message_id = 0
        print(color_log("Bonkbot is updating, Bot turned off", "yellow"))


# Handles failed transactions from BonkBot
@app.on_edited_message(
    filters.chat(bonkbotmcqueen) & filters.regex("Swap failed|No route found")
)
async def listen_bonkbot_swap_failed(client, message):
    global last_buy_message_id
    global balance
    async with state_lock:

        # If the transaction was the initial buy, we reset the state
        if "Auto Buy" in message.text:
            last_buy_message_id = 0
            print(color_log("Token Buy failed", "light_red"))

        # "No route found" is a similar case as "Token not found"
        elif "No route found" in message.text:
            print(color_log("No route found", "light_red"))
        else:
            # If the transaction was a sell, we keep retrying
            print(color_log("Token Sell failed retrying...", "light_red"))
            buy_message = await app.get_messages(bonkbotmcqueen, last_buy_message_id)
            await buy_message.click("Sell 100%")


app.run()
