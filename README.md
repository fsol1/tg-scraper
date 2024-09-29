# tg-scraper

**tg-scraper** is a trading bot which to listen for messages from specific Telegram channels, parse them for Solana addresses, and forward the addresses to **BonkBot**.

**⚠️ Warning: This bot is for educational purposes only. You should not expect to make a profit from it, and I am not responsible for any potential losses.**

## Context

Between November 2023 and March 2024, the Solana ecosystem was booming and at the core of it, there were callers (influencers) who shared token addresses (think of it like a stock ticker) within their Telegram channels, each of which had thousands of subscribers. These posts typically caused the value of the shared tokens to surge within seconds to minutes, as people quickly bought into the tokens. 

The purpose of this bot was to purchase the token immediately after the caller posted it, before others could, hold it briefly, and then sell it for a profit. As other bots are now way faster than this one, I decided to open source this project for educational purposes.

## Demo

Here is a demonstration of the bot in action: a token address is sent through a test channel, the bot detects it, quickly buys the token, and then sells it 10 seconds later for a potential profit.

https://github.com/user-attachments/assets/e03f5d52-1b59-462e-bbef-9094a2082821



## Getting Started

### What you'll need
-   A **Telegram account** with access to **BonkBot** (McQueen)
-   **Telegram API credentials** (API ID and API Hash)
-   A **Telegram private channel** to use as a test channel
-   A list of **Telegram channels** you want the bot to listen to

### Setting Up the Python Environment (Linux and macOS)

Create a virtual environment: 
```bash
python3 -m venv myenv
```
Activate the virtual environment:
```bash
source myenv/bin/activate
```
Install the required dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Retrieve the Channels Your Account Is Subscribed To

This command will print out all the channels your account is subscribed to, along with their IDs:
```bash
python dialogs.py
```

You can then place those IDs in `util.py` within the `ids_to_names` dictionary.

### Fill Up the `.env` File

```text
API_ID=  # Your Telegram API ID
API_HASH=  # Your Telegram API Hash
PUBKEY=  # Your BonkBot public key
TEST_CHANNEL=  # ID of your test channel
HOLDING_TIME=  # Holding time for trades in seconds
BAN_WORDS=potatotest,bananatest  # List of banned words
```


### Setting Up BonkBot

- Make sure you have some SOL in your wallet.
- Configure the bot settings as needed.
- Make sure to enable the auto-buy feature.

### Running the bot
Start the bot:
```bash
python lanaos.py
```
Once running, the bot will begin listening for messages and will log every trade both in the terminal and in the `logs.csv` file.

## Performance and Deployment
