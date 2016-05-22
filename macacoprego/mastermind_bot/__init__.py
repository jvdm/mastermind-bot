import json
import re
import logging
import functools

import aiohttp
from aiohttp import MsgType, ws_connect
from aslack.slack_bot import SlackBot
from aslack.utils import truncate
import asyncio

from .version_info import __version__


log = logging.getLogger(__name__)


def get_api_url(api, **kwds):
    return ('https://mastermind-macacoprego.herokuapp.com/{}/'
            .format(api.format(**kwds)))


class MastermindBot(SlackBot):

    VERSION = __version__

    loop = None

    players = {}

    # FIXME We need to overwrite this method because we want to access
    #       the socket later on.  We changed only the `self.socket`
    #       line and references to `logger`.

    async def join_rtm(self, filters=None):
        """Join the real-time messaging service."""
        if filters is None:
            filters = self.MESSAGE_FILTERS
        url = await self.get_socket_url()
        log.debug('Connecting to %r', url)
        async with ws_connect(url) as socket:
            # Export the socket to the class:
            self.socket = socket
            first_msg = await socket.receive()
            self._validate_first_message(first_msg)
            async for message in socket:
                if message.tp == MsgType.text:
                    result = await self.handle_message(message, filters)
                    if result is not None:
                        log.info(
                            'Sending message: %r',
                            truncate(result, max_len=50),
                        )
                        socket.send_str(result)
                elif message.tp in (MsgType.closed, MsgType.error):
                    if not socket.closed:
                        await socket.close()
                    break
        log.info('Left real-time messaging.')

    def send_message(self, channel, text, **kwds):
        kwds['channel'] = channel
        kwds['text'] = text
        payload = {'type': 'message', 'id': next(self._msg_ids)}
        payload.update(kwds)
        self.socket.send_str(json.dumps(payload))

    def _reply_to(self, msg, text):
        log.info(msg)
        return {'channel': msg['channel'],
                'text': '<@{user}>: {text}'
                    .format(user=msg['user'], text=text)}

    def _filter_command(self, msg, command):
        return (self.message_is_to_me(msg) and
                msg['text'].lstrip(self.address_as).startswith(command))

    def filter_create_command(self, msg):
        return self._filter_command(msg, 'create')

    def _reply_callback(self, msg, fut):
        try:
            text = fut.result()
        except:
            text = ('sorry man, something bad '
                    'happend ({})'.format(fut.exception()))
            log.exception('request failed')
        self.send_message(**self._reply_to(msg, text))

    async def dispatch_create_command(self, msg):
        players = re.findall(r'<@\w+>', msg['text'].lstrip(self.address_as))
        # The creator is just another player.
        players.insert(0, '<@{}>'.format(msg['user']))
        asyncio.ensure_future(self.create_game(msg, players),
                              loop=self.loop) \
               .add_done_callback(functools.partial(self._reply_callback, msg))
        return self._reply_to(msg, 'nice, a new game is on the way...')

    async def create_game(self, msg, players):
        log.info('creating game for %s', players)
        api_url = get_api_url('games')
        with aiohttp.ClientSession() as session:
            async with session.post(api_url, data={'players_count': len(players)}) \
                    as resp:
                game_info = await resp.json()
            return ("done guys, game #{id} was created with "
                    "{players_count} players ({names}), you may "
                    "make a guess to this game by sending messages like "
                    "'guess #{id} <your guess>'."
                    .format(names=', '.join(players), **game_info))

    MESSAGE_FILTERS = {
        filter_create_command: dispatch_create_command}


def main():

    logging.basicConfig(
        datefmt='%H:%M:%S',
        format='%(asctime)s %(name)s [%(levelname)s] %(message)s',
        level=logging.INFO)

    token = 'xoxb-44792020947-fGA0luNrhKyIpr6PyN6PksKN'
    loop = asyncio.get_event_loop()
    bot = loop.run_until_complete(MastermindBot.from_api_token(token))
    # FIXME Usually we would pass this to __init__, but this aslack
    #       lib is very poorly designed.
    bot.loop = loop
    loop.run_until_complete(bot.join_rtm())
