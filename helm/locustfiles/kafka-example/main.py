# -*- coding: utf-8 -*-

import os
import random
import string
import time

from lib.additional_handlers import additional_success_handler, additional_failure_handler
from locust import User, task, events, between

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from lib.kafka_client import KafkaClient

WORK_DIR = os.path.dirname(__file__)

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka-example-cp-kafka.default.svc.cluster.local:9092")
SCHEMA_REGISTRY = os.getenv("SCHEMA_REGISTRY", "http://kafka-example-cp-schema-registry.default.svc.cluster.local:8081")

QUIET_MODE = True if os.getenv("QUIET_MODE", "true").lower() in ['1', 'true', 'yes'] else False
TASK_DELAY = int(os.getenv("TASK_DELAY", "0"))

print("Sending messages to " + os.environ['TOPIC'] + " on " + BOOTSTRAP_SERVERS)

# register additional logging handlers
if not QUIET_MODE:
    events.request_success += additional_success_handler
    events.request_failure += additional_failure_handler


class KafkaUser(User):
    client = None

    wait_time = between(1, 2.5)

    def __init__(self, *args, **kwargs):
        super(KafkaUser, self).__init__(*args, **kwargs)
        if not KafkaUser.client:

            value_schema_str = """
            {
              "fields": [
                {
                  "name": "task",
                  "type": "string"
                },
                {
                  "name": "assignee",
                  "type": "string"
                },
                {
                  "name": "duration",
                  "type": "int"
                },
                {
                  "name": "creationTimestamp",
                  "type": "long"
                }
              ],
              "name": "ToDo",
              "namespace": "io.codebrews.todoevents",
              "type": "record"
            }
            """

            key_schema_str = """
            {
               "namespace": "my.test",
               "name": "key",
               "type": "record",
               "fields" : [
                 {
                   "name" : "name",
                   "type" : "string"
                 }
               ]
            }
            """

            schema_registry_client = SchemaRegistryClient({'url': SCHEMA_REGISTRY})

            key_serializer = AvroSerializer(schema_registry_client, key_schema_str)
            value_serializer = AvroSerializer(schema_registry_client, value_schema_str)

            KafkaUser.client = KafkaClient(
                bootstrap_servers=BOOTSTRAP_SERVERS,
                key_serializer=key_serializer,
                value_serializer=value_serializer,
            )

        value = {
            "task": self.random_message(),
            "assignee": "me",
            "duration": 5,
            "creationTimestamp": int(time.time())
        }
        key = {"name": self.timestamped_message()}
        self.client.produceSilently(os.environ['TOPIC'], key=key, value=value)

    def random_message(self, min_length=32, max_length=128):
        return ''.join(random.choice(string.ascii_uppercase) for _ in range(random.randrange(min_length, max_length)))

    def timestamped_message(self):
        return f"{time.time() * 1000}:" + ("kafka" * 24)[:random.randint(32, 128)]

    @task
    def task(self):
        value = {
            "task": self.random_message(),
            "assignee": "me",
            "duration": 5,
            "creationTimestamp": int(time.time())
        }
        key = {"name": self.timestamped_message()}
        self.client.produce(os.environ['TOPIC'], key=key, value=value)

    def on_stop(self):
        self.client.producer.flush(5)