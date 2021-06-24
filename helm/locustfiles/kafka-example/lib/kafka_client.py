# -*- coding: utf-8 -*-

import time
import os
from locust import events
from confluent_kafka import avro
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import (MessageField, SerializationContext)
import io
from functools import partial

class KafkaClient:

    def __init__(self, bootstrap_servers=None, key_serializer=None, value_serializer=None):
        print("creating message sender with params: " + str(locals()))
        self._value_serializer = value_serializer
        self.producer = SerializingProducer({
            'bootstrap.servers': bootstrap_servers,
            'key.serializer': key_serializer,
            'value.serializer': value_serializer,
        })

    def ack(self, err, msg, topic, start_time, response_length):
        end_time = time.monotonic()
        elapsed_time = int((end_time - start_time) * 1000)

        if err is not None:
            print("Failed to deliver message: %s" % (str(err)))
            request_data = dict(
                request_type="ENQUEUE",
                name=topic,
                response_time=elapsed_time,
                exception=err
            )
            self.__fire_failure(**request_data)
        else:
            request_data = dict(
                request_type="ENQUEUE",
                name=topic,
                response_time=elapsed_time,
                response_length=response_length
            )
            self.__fire_success(**request_data)

    def __fire_failure(self, **kwargs):
        events.request_failure.fire(**kwargs)

    def __fire_success(self, **kwargs):
        events.request_success.fire(**kwargs)

    def produce(self, topic, key=None, value=None):
        start_time = time.monotonic()

        ctx = SerializationContext(topic, MessageField.VALUE)
        raw_bytes = self._value_serializer(value, ctx)

        self.producer.produce(
            topic=topic,
            value=value,
            key=key,
            on_delivery=partial(self.ack, topic=topic, start_time=start_time, response_length=len(raw_bytes))
        )
        self.producer.poll()

    def produceSilently(self, topic, key=None, value=None):
        self.producer.produce(
            topic=topic,
            value=value,
            key=key,
        )
        self.producer.poll()

    def flush(self, timeout):
        self.producer.flush(timeout)