import asyncio
from lib.api import HubitatApi
from lib.logger import logger
from lib.config import config

logger.info('booting application')


if __name__ == "__main__":
    try:
        logger.info('starting services')

        loop = asyncio.get_event_loop()
        event_queue = asyncio.Queue()
        cmd_queue = asyncio.Queue()
        api = HubitatApi()
        loop.create_task(api.publish_homeassistant_commands(cmd_queue))
        loop.create_task(api.send_commands_to_hubitat(cmd_queue, event_queue))
        loop.create_task(api.publish_hubitat_events(event_queue))
        loop.create_task(api.send_events_to_mqtt(event_queue))
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        logger.info('user requested shutdown. terminating')
        loop.stop()
