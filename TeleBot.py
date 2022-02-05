import pdb
from typing import List
import re
import requests
import json
import model.Constants as const
from model.Reqest.CommandRequest import SetCommandRequest, BotCommandScope, CommandDto
from model.Reqest.ForwardReqest import ForwardRequest
from model.Response.ErrorResponse import error_from_dict
from model.Response.ForwardResponse import ForwardResponse, forward_from_dict
from model.Response.GetMeResponse import GetMeResponse, get_me_response_from_dict
from model.Response.SuccessResponse import success_from_dict
from url.UrlBuilder import SendMessageUrl, UpdateUrl

from model.Update import UpdateType, Update


class TeleBot:
    _commands = {}
    _callback = {}
    _text = {}
    headers = {
        'Content-Type': 'application/json'
    }

    def __init__(self, token, limited=None):
        self.base = f"{const.BASE_URL}{token}/"
        self.limited = limited

    def poll(self, update=None, timeout=1200, allowed_types=None):
        lastUpdate = None
        while True:
            if lastUpdate is None:
                response = self.get_updates(offset=-1, timeout=timeout, allowed_types=allowed_types)
            else:
                response = self.get_updates(offset=lastUpdate.getNextUpdateID(), timeout=timeout,
                                            allowed_types=allowed_types)

            updates = self.generate_updates(response)

            if updates:
                for item in updates:
                    lastUpdate = item
                    self.process_update(item)
                    if update is not None:
                        update(item)

    def add_command(self, command=None, regex=None):
        def decorator(func):
            if command is not None:
                self._commands[command] = func
            else:
                if isinstance(regex, list):
                    for t in regex:
                        self._text[regex] = func
                else:
                    self._text[regex] = func

        return decorator

    def add_callback(self, callback_data):
        def decorator(func):
            self._callback[callback_data] = func

        return decorator

    def get_updates(self, offset, timeout, allowed_types) -> {}:
        if allowed_types is None:
            allowed_types = [UpdateType.MESSAGE]

        get_update_url = UpdateUrl(self.base) \
            .timeout(timeout) \
            .allowed_updates(allowed_types) \
            .offset(offset, condition=offset is not None) \
            .build()

        response = requests.request("GET", get_update_url, headers={}, data={})
        response = json.loads(response.content)

        return response

    def generate_updates(self, response) -> List[Update]:

        if response.get('ok', False) is True:
            return list(map(lambda update: Update(response=update), response["result"]))
        else:
            raise ValueError(response['error'])

    def process_update(self, item):
        if item.message.fromUser.getID() != int(self.limited):
            return
        if len(item.message.entities) != 0 and item.message.entities[0].type == "bot_command" and \
                item.getUpdateType() == UpdateType.MESSAGE and item.message.entityType():
            command = item.message.text[item.message.entities[0].offset:item.message.entities[0].length]
            if self._commands.get(command): self._commands.get(command)(item.message)
        elif item.message.text:
            for p in self._text.keys():
                r = re.compile(p)
                if re.fullmatch(r, item.message.text.lower()):
                    self._text.get(p)(item.message)
        elif item.getUpdateType() == UpdateType.CALLBACK:
            callback = item.callback.message.replyMarkup.keyboards[0].callbackData.split("@")[1]
            self._callback.get(callback)(item.message)
        else:
            print("DEAD ☠️")

    def get_me(self) -> GetMeResponse:
        """
        :return: Returns information about the bot using the GetMeResponse class
        """
        url = f'{self.base}getMe'
        response = requests.post(url, headers={}, data={})
        return get_me_response_from_dict(response.text)

    def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                     disable_notification=None, reply_to_message_id=None,
                     allow_sending_without_reply=None, reply_markup=None):
        """
        :param chat_id: Unique identifier for the target chat or username of the target channel
        :param text: Text of the message to be sent, 1-4096 characters after entities parsing
        :param parse_mode: Mode for parsing entities in the message text allowing for bold and italic formats
        :param disable_web_page_preview: Disables link previews for links in this message
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :param reply_markup: Pass True, if the message should be sent even if the specified replied-to message is not found
        """
        sendMessageUrl = SendMessageUrl(self.base).text(text).chat_id(chat_id).parse_mode(parse_mode) \
            .disable_web_page_preview(disable_web_page_preview) \
            .disable_notification(disable_notification) \
            .reply_to_message_id(reply_to_message_id) \
            .allow_sending_without_reply(allow_sending_without_reply) \
            .reply_markup(reply_markup).build()
        requests.request("POST", sendMessageUrl, headers={}, data={})

    def forward_messaged(self, chat_id, from_chat_id, message_id: int,
                         disable_notification: bool = None, protect_content: bool = None) -> ForwardResponse:
        """
        Use this method to forward messages of any kind. Service messages can't be forwarded.
        On success, the sent Message is returned.
        :param chat_id: Unique identifier for the target chat or username of the target channel
        :param from_chat_id: Unique identifier for the chat group where the original message was sent
        :param message_id: Message id in the chat group specified in from_chat_id
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :param protect_content: Protects the contents of the forwarded message from forwarding and saving
        :return: ForwardResponse containing the message
        """
        url = f'{self.base}forwardMessage'
        request_body = ForwardRequest()
        request_body = request_body.chat_id(chat_id).from_chat_id(from_chat_id).message_id(message_id). \
            disable_notification(disable_notification).protect_content(protect_content).build()

        response = requests.post(url, headers={}, data=request_body)
        return forward_from_dict(response.text)

    def set_my_commands(self, commands: [CommandDto], scope: BotCommandScope = None, language_code: str = None):
        url = f'{self.base}setMyCommands'
        request_body = SetCommandRequest().commands(commands).scope(scope) \
            .language_code(language_code).build()

        response = requests.post(url, headers=self.headers, data=json.dumps(request_body))

        if response.status_code != 200:
            return error_from_dict(response.text)
        else:
            return success_from_dict(response.text)

    def send_photo(self, chat_id, file):
        up = {'photo': ("i.png", open(file, 'rb'), "multipart/form-data")}
        url = self.base + f"sendPhoto"
        requests.post(url, files=up, data={
            "chat_id": chat_id,
        })
