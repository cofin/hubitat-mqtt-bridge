from .logger import logger
from .config import config
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_0, QOS_1, QOS_2
import websockets
import json
import hbmqtt
import aiohttp


class HubitatApi:
    EVENT_SOCKET_URI = f"ws://{config.hubitat_host}/eventsocket"
    API_TOKEN = f"{config.hubitat_maker_token}"
    MQTT_URI = f"mqtt://{config.mqtt_username}:{config.mqtt_password}@{config.mqtt_host}:{config.mqtt_port}"
    CMD_TOPIC = "+/+/+/+/cmd"
    MQTT_PREFIX = 'ha-dev/hubitat'
    HUBITAT_HOST = config.hubitat_host
    APP_ID = config.hubitat_maker_app_id

    @staticmethod
    async def _enqueue(message, queue):
        logger.info('publishing message to queue.')
        await queue.put(message)

    async def send_events_to_mqtt(self, queue):
        uri = self.EVENT_SOCKET_URI
        async with websockets.connect(uri) as ws:
            logger.info("connected to event socket")
            async for msg in ws:
                logger.info(f"received message: {msg}")
                await self._enqueue(msg, queue)

    async def publish_hubitat_events(self, queue):
        while True:
            message = await queue.get()
            if type(message) is dict:
                event = message
            else:
                event = json.loads(message)
            # dump the event straight to mqtt
            topic = f"{self.MQTT_PREFIX}/{event['deviceId']}/{event['name']}/state"
            payload = event['value']
            mqtt_client = hbmqtt.client.MQTTClient(
                config={'keep_alive': 30, 'ping_delay': 1})
            await mqtt_client.connect(uri=self.MQTT_URI)
            await mqtt_client.publish(topic, str(payload).encode(), qos=QOS_1)
            await mqtt_client.disconnect()
            logger.info(f"published message: {topic} {payload}")

    async def send_commands_to_hubitat(self, queue, event_queue):
        url_base = f"http://{self.HUBITAT_HOST}/apps/api/{self.APP_ID}/devices"
        while True:
            message = await queue.get()
            device_id = message['device_id']
            url = f"{url_base}/{device_id}/{message['command']}?access_token={self.API_TOKEN}"
            print(url)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json(content_type=None)  # content_type='text/html;charset=utf-8')
                    if resp.status == 200:
                        logger.info(f"send command to hubitat: {url}\n   output: {data}")

                        # success
                        print(data)
                        if data:
                            for attr in data['attributes']:
                                if attr['name'] != 'checkInterval':
                                    print(f"{device_id}/{attr['name']}/state {attr['currentValue']}")
                                    event = {'source': 'EVENT',
                                             'name': attr['name'],
                                             'value': attr['currentValue'],
                                             'deviceId': device_id}
                                    await self._enqueue(event, event_queue)

                    else:
                        logger.info(f"error sending command to hubitat: {data}")

    async def publish_homeassistant_commands(self, queue):
        mqtt_config = {
            'keep_alive': 10,
            'ping_delay': 1,
            'default_qos': 2,
            'default_retain': True,
            'auto_reconnect': True,
            'reconnect_max_interval': 5,
            'reconnect_retries': 10,
            'topics': {
                'hubitat/dev/+/+/cmd': {'qos': 2, 'retain': True}
            }
        }
        mqtt_client = MQTTClient(
            config=mqtt_config)
        await mqtt_client.connect(uri=self.MQTT_URI)
        topic = f"{self.MQTT_PREFIX}/+/+/cmd"
        await mqtt_client.subscribe([(topic,
                                      hbmqtt.mqtt.constants.QOS_2)])
        try:
            while True:
                message = await mqtt_client.deliver_message()
                device_id = message.topic.split('/')[2]
                capability = message.topic.split('/')[3]
                if capability == 'level':
                    cmd = f"setLevel/{message.data.decode()}"
                elif capability == 'switch':
                    cmd = f"{message.data.decode()}"
                else:
                    cmd = f"{capability}/{message.data.decode()}"
                payload = {'device_id': device_id,
                           'command': cmd}
                logger.info(f"prepped command: {payload}")
                await queue.put(payload)
        finally:
            await mqtt_client.unsubscribe([topic])
            await mqtt_client.disconnect()

