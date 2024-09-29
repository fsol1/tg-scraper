import os

from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

app = Client("my_account", api_id=api_id, api_hash=api_hash)


# Prints out all the dialogs from your Telegram account with their id
async def main():
    async with app:
        async for dialog in app.get_dialogs():
            print(dialog.chat.title or dialog.chat.first_name, dialog.chat.id)


app.run(main())
