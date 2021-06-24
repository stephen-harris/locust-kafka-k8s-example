## Set up Kafka (optional)

Install Kafka

```
helm template --name-template=kafka-example kafka > kafka.yaml
k apply -f kafka.yaml
```

Access control centre:

```
k port-forward svc/kafka-example-cp-control-center 9021:9021
```

Go to the control centre <http://localhost:9021/>, and wait for the cluster to be healthy. Then create a topic. See `helm/locustfiles/kafka-example/main.py` for the key and value schema.


## Install locust

Update the `helm/values.yaml` file to pass in the topic name. Optionally configure the broker & schema registry.

Then install locust:

```
cd helm
helm template --name-template=kafka-example helm > locust.yaml
k apply -f locust.yaml
k rollout restart deployment/kafka-example-locust-master
k rollout restart deployment/kafka-example-locust-worker
```

Port forward to locust:

```
k port-forward svc/kafka-example-locust 8089:8089
```

Go to <http://localhost:8089/> to start the load test.


## Modifying the load test

The `locustfile` is `helm/locustfiles/kafka-example/main.py`. Once you make any changes, reapply the helm chart and restart the locust nodes:

```
cd helm
helm template --name-template=kafka-example helm > locust.yaml
k apply -f locust.yaml
k rollout restart deployment/kafka-example-locust-master
k rollout restart deployment/kafka-example-locust-worker
```