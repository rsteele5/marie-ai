from typing import Any, List

from marie.messaging.rabbitmq import BlockingPikaClient
from marie.messaging.toast_handler import ToastHandler
from pika.exchange_type import ExchangeType


class AmazonMQToastHandler(ToastHandler):
    """
    Amazon Toast Handler that publishes events to Amazon MQ
    TODO: Need to add support for SNS and make this asynchynous.
    """

    def __init__(self, config: Any, **kwargs: Any):
        self.config = config

    def get_supported_events(self) -> List[str]:
        return ["*"]

    async def notify(self, notification: Any, **kwargs: Any) -> bool:
        if not self.config or not self.config["enabled"]:
            return False

        try:
            msg_config = self.config
            exchange = "marie.events"
            queue = "events"
            routing_key = notification["event"] if "event" in notification else "*"

            client = BlockingPikaClient(conf=msg_config)

            # Declare the destination exchange with the topic exchange type to allow routing
            client.exchange_declare(
                exchange, durable=True, exchange_type=ExchangeType.topic
            )
            client.declare_queue(queue, durable=True)
            # Bind the queue to the destination exchange
            client.channel.queue_bind(queue, exchange=exchange, routing_key=routing_key)
            client.publish_message(
                exchange=exchange, routing_key=routing_key, message=notification
            )

            client.close()
            return True
        except Exception as e:
            raise e
