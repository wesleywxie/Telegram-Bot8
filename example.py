import os

from Bot.TeleBot import TeleBot
from Bot.Model.Message import Message, ParseMode
from Bot.Model.Update import Update

API_KEY = os.getenv('telegramApiKey')
bot = TeleBot(API_KEY)


# Just listening to updated
def update(update: Update):
    print(update)


# Adds command into telegram menu and listen to multiple commands
@bot.add_command_menu_helper(command=["/hello", "/hallo"], description="Trigger hello message")
def endServer(message: Message):
    bot.send_message(message.chat.getID(), "Hello")


# Just listens to commands
@bot.add_command_helper(command="/hi")
def endServer(message: Message):
    bot.send_message(message.chat.getID(), "Hello")


# Listens to single command
@bot.add_command_menu_helper(command="/bye", description="Trigger the bye message")
def endServer(message: Message):
    bot.send_message(message.chat.getID(), "Bye")


# Listen to regex based messages
@bot.add_regex_helper(regex="^hi$")
def endServer(message: Message):
    bot.send_message(message.chat.getID(), "Hello")


# Sending bold message and types is possible
@bot.add_regex_helper(regex="^bold$")
def send_bold(message: Message):
    bot.send_message(message.chat.getID(), "<b>Hello</b>", parse_mode=ParseMode.HTML.value)


# Forwarding message in telegram bot
@bot.add_regex_helper(regex=["^forward message$", "^fwd message$"])
def send_bold(message: Message):
    print(bot.forward_messaged(chat_id=message.chat.getID(), from_chat_id=message.chat.getID(),
                               message_id=message.get_id()))


# Getting information about the bot
@bot.add_regex_helper(regex="^get me$")
def send_bold(message: Message):
    info = bot.get_me()
    bot.send_message(message.chat.getID(), info.result.username)


# Delete all the commands in the bot
@bot.add_regex_helper(regex="^delete my command$")
def send_bold(message: Message):
    response = bot.delete_my_commands()
    print(response.to_dict())


# Printing the commands
print(bot.get_my_commands().to_dict())

# To starting the bot listening
bot.poll(update=update)
