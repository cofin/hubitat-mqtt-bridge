import asyncio
import websockets
from lib.api import HubitatApi
from lib.logger import logger
from lib.config import config

logger.info('booting application')


def exception_handler(loop, context):
    # first, handle with default handler
    loop.default_exception_handler(context)

    exception = context.get('exception')
    if isinstance(exception, websockets.exceptions.ConnectionClosed):
        logger.fatal('hubitat websocket closed.')
    else:
        logger.fatal(context)
    loop.stop()


if __name__ == "__main__":
    logger.info('starting services')
    app_loop = asyncio.get_event_loop()
    app_loop.set_exception_handler(exception_handler)
    event_queue = asyncio.Queue()
    cmd_queue = asyncio.Queue()
    api = HubitatApi()
    app_loop.create_task(api.publish_homeassistant_commands(cmd_queue))
    app_loop.create_task(api.send_commands_to_hubitat(cmd_queue))
    # loop.create_task(api.publish_configs())
    app_loop.create_task(api.publish_hubitat_events(event_queue))
    app_loop.create_task(api.send_events_to_mqtt(event_queue))
    app_loop.run_forever()

