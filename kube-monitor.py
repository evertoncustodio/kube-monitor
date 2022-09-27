import logging

import argument
from pyexecutor import Executor
from tabulate import tabulate
import json


class Resource:
    def __init__(self, cpu, memory):
        self.cpu = cpu
        self.memory = memory

    def get_info(self):
        return f"CPU: {self.cpu}; Memory: {self.memory}"

    def get_cpu(self):
        if self.cpu is None:
            return 0
        elif "m" in str(self.cpu):
            return int(str(self.cpu).split("m")[0])
        elif "n" in str(self.cpu):
            return int(str(self.cpu).split("n")[0]) / 1000 / 1000
        else:
            return int(self.cpu)

    def get_memory(self):
        if self.memory is None:
            return 0
        elif "Ki" in str(self.memory):
            return int(int(str(self.memory).split("Ki")[0]) / 1000)
        elif "Mi" in str(self.memory):
            return int(str(self.memory).split("Mi")[0])
        else:
            return int(self.memory)


class Container:
    def __init__(self, name, usage, requests, limits):
        self.name = name
        self.usage = usage
        self.requests = requests
        self.limits = limits

    def get_info(self):
        return f"Container: {self.name} " \
               f"CPU Req: {self.requests.cpu} " \
               f"CPU Lim: {self.limits.cpu} " \
               f"Memory Req: {self.requests.memory} " \
               f"Memory Lim: {self.limits.memory} "


class Pod:
    def __init__(self, namespace, name, node_name):
        self.namespace = namespace
        self.name = name
        self.containers = {}
        self.id = f"{namespace}/{name}"
        self.node_name = node_name

    def add_container(self, container):
        self.containers[container.name] = container

    def get_containers(self):
        return self.containers

    def get_info(self):
        return f"Pod {self.namespace}/{self.name}\n" \
               f" {self.get_container_info()}"

    def get_container_info(self):
        info = ""
        for name in self.containers:
            info += self.containers[name].get_info() + "\n"

        return info

    def get_resource_utilization(self):
        cpu = 0
        memory = 0

        for name in self.containers:
            container = self.containers[name]
            cpu += container.usage.get_cpu()
            memory += container.usage.get_memory()

        return Resource(cpu, memory)

    def get_resource_limits(self):
        cpu = 0
        memory = 0

        for name in self.containers:
            container = self.containers[name]
            cpu += container.limits.get_cpu()
            memory += container.limits.get_memory()

        return Resource(cpu, memory)

    def get_resource_requests(self):
        cpu = 0
        memory = 0

        for name in self.containers:
            container = self.containers[name]
            cpu += container.requests.get_cpu()
            memory += container.requests.get_memory()

        return Resource(cpu, memory)


class Node:
    def __init__(self, name, cpu_capacity, cpu_utilization, memory_capacity, memory_utilization):
        self.name = name
        self.cpu_capacity = cpu_capacity
        self.memory_capacity = memory_capacity
        self.cpu_utilization = cpu_utilization
        self.memory_utilization = memory_utilization
        self.pods = {}

    def get_info(self):
        return (f"Node: {self.name}\n"
                f"CPU Capacity: {self.get_cpu_capacity()}\n"
                f"CPU Utilization: {self.get_cpu_utilization()}\n"
                f"CPU Utilization (%): {self.get_cpu_utilization_perc()}\n"
                f"CPU Requests: {self.get_total_requests().get_cpu()}\n"
                f"CPU Requests (%): {self.get_cpu_requests_perc()}\n"
                f"CPU Limits: {self.get_total_limits().get_cpu()}\n"
                f"CPU Limits (%): {self.get_cpu_limits_perc()}\n"
                f"Memory Capacity: {self.get_memory_capacity()}\n"
                f"Memory Utilization: {self.get_memory_utilization()}\n"
                f"Memory Utilization (%): {self.get_memory_utilization_perc()}\n"
                f"Memory Requests: {self.get_total_requests().get_memory()}\n"
                f"Memory Requests (%): {self.get_memory_requests_perc()}\n"
                f"Memory Limits: {self.get_total_limits().get_memory()}\n"
                f"Memory Limits(%): {self.get_memory_limits_perc()}\n")

    def get_cpu_capacity(self):
        return int(self.cpu_capacity) * 1000

    def get_cpu_utilization(self):
        return int(int(str(self.cpu_utilization.split("n")[0])) / (1000 * 1000))

    def get_memory_capacity(self):
        return int(int(str(self.memory_capacity).split("Ki")[0]) / 1000)

    def get_memory_utilization(self):
        return int(int(str(self.memory_utilization).split("Ki")[0]) / 1000)

    def get_cpu_utilization_perc(self):
        cpu_utilization = int(str(self.cpu_utilization).split("n")[0])
        cpu_capacity = int(self.cpu_capacity) * 1000 * 1000 * 1000
        cpu_perc = cpu_utilization * 100 / cpu_capacity
        return int(cpu_perc)

    def get_memory_utilization_perc(self):
        memory_utilization = int(str(self.memory_utilization).split("Ki")[0])
        memory_capacity = int(str(self.memory_capacity).split("Ki")[0])
        memory_perc = memory_utilization * 100 / memory_capacity
        return int(memory_perc)

    def get_cpu_requests_perc(self):
        return int(self.get_total_requests().get_cpu() * 100 / self.get_cpu_capacity())

    def get_cpu_limits_perc(self):
        return int(self.get_total_limits().get_cpu() * 100 / self.get_cpu_capacity())

    def get_memory_requests_perc(self):
        return int(self.get_total_requests().get_memory() * 100 / self.get_memory_capacity())

    def get_memory_limits_perc(self):
        return int(self.get_total_limits().get_memory() * 100 / self.get_memory_capacity())

    def add_pod(self, pod):
        self.pods[pod.id] = pod

    def get_total_requests(self):
        cpu_total = 0
        memory_total = 0

        for pod_id in self.pods:
            pod = self.pods[pod_id]
            resources = pod.get_resource_requests()
            cpu_total += resources.cpu
            memory_total += resources.memory

        return Resource(cpu_total, memory_total)

    def get_total_limits(self):
        cpu_total = 0
        memory_total = 0

        for pod_id in self.pods:
            pod = self.pods[pod_id]
            resources = pod.get_resource_limits()
            cpu_total += resources.cpu
            memory_total += resources.memory

        return Resource(cpu_total, memory_total)

    def get_pod_info(self):
        info = ""
        for p in self.pods:
            pod = self.pods[p]
            info += f" {pod.get_info()}\n"

        return info


def load_nodes():
    nodes = json.loads(kubectl.run("get node -o json"))
    for item in nodes["items"]:
        metadata = item["metadata"]
        name = metadata["name"]

        status = item["status"]
        capacity = status["capacity"]
        cpu_capacity = capacity["cpu"]
        memory_capacity = capacity["memory"]

        top = json.loads(kubectl.run(f"get --raw /apis/metrics.k8s.io/v1beta1/nodes/{name}"))
        usage = top["usage"]
        cpu_utilization = usage["cpu"]
        memory_utilization = usage["memory"]

        node = Node(name, cpu_capacity, cpu_utilization, memory_capacity, memory_utilization)
        node_dict[node.name] = node


def load_pods():
    pods = json.loads(kubectl.run("get pod -A -o json"))
    for item in pods["items"]:
        metadata = item["metadata"]
        name = metadata["name"]
        namespace = metadata["namespace"]
        spec = item["spec"]
        node_name = spec["nodeName"]

        status = item.get("status")
        if "Running" not in status.get("phase"):
            continue

        pod = Pod(namespace, name, node_name)
        pod_dict[pod.id] = pod

        node = node_dict[node_name]
        node.add_pod(pod)

        top_containers = {}
        top = json.loads(kubectl.run(f"get --raw /apis/metrics.k8s.io/v1beta1/namespaces/{namespace}/pods/{name}"))

        for container_json in top["containers"]:
            container_name = container_json["name"]
            top_containers[container_name] = container_json["usage"]

        for container_json in spec["containers"]:
            container_name = container_json["name"]

            usage = top_containers[container_name]
            cpu_usage = usage["cpu"]
            memory_usage = usage["memory"]

            resources = container_json.get("resources")

            cpu_limits = 0
            memory_limits = 0
            if "limits" in resources:
                limits = resources.get("limits")
                cpu_limits = limits.get("cpu")
                memory_limits = limits.get("memory")

            cpu_requests = 0
            memory_requests = 0
            if "requests" in resources:
                requests = resources.get("requests")
                cpu_requests = requests.get("cpu")
                memory_requests = requests.get("memory")

            res_usage = Resource(cpu_usage, memory_usage)
            res_requests = Resource(cpu_requests, memory_requests)
            res_limits = Resource(cpu_limits, memory_limits)
            container = Container(container_name, res_usage, res_requests, res_limits)

            pod.add_container(container)


def show_nodes(node_name):
    headers = [
        "Name",
        "CPU Util(%)",
        "CPU Req(%)",
        "CPU Lim(%)",
        "Memory Util(%)",
        "Memory Req(%)",
        "Memory Lim(%)"
    ]

    table = []
    for n in node_dict:
        if node_name != '' and node_name not in str(n):
            continue

        node = node_dict[n]
        line = [
            node.name,
            node.get_cpu_utilization_perc(),
            node.get_cpu_requests_perc(),
            node.get_cpu_limits_perc(),
            node.get_memory_utilization_perc(),
            node.get_memory_requests_perc(),
            node.get_memory_limits_perc()
        ]
        table.append(line)

    print(tabulate(table, headers))


def show_pods(node, namespace):
    headers = [
        "Node",
        "Namespace",
        "Name",
        "CPU Util(m)",
        "CPU Req(m)",
        "CPU Lim(m)",
        "Memory Util(Mi)",
        "Memory Req(Mi)",
        "Memory Lim(Mi)"
    ]

    table = []
    for p in pod_dict:
        pod = pod_dict[p]

        if node != "" and node not in pod.node_name:
            continue

        if namespace != "" and namespace not in pod.namespace:
            continue

        line = [
            pod.node_name,
            pod.namespace,
            pod.name,
            pod.get_resource_utilization().get_cpu(),
            pod.get_resource_requests().get_cpu(),
            pod.get_resource_limits().get_cpu(),
            pod.get_resource_utilization().get_memory(),
            pod.get_resource_requests().get_memory(),
            pod.get_resource_limits().get_memory()
        ]
        table.append(line)

    print(tabulate(table, headers))


node_dict = {}
pod_dict = {}

log = logging.getLogger()
log.setLevel(logging.FATAL)
kubectl = Executor("kubectl", logger=log)

f = argument.Arguments()
f.option("node", "", help="node name", abbr="nd")
f.option("namespace", "", help="namespace", abbr="ns")


def main():
    arguments, errors = f.parse()
    node = arguments["node"]
    namespace = arguments["namespace"]

    load_nodes()
    load_pods()

    show_nodes(node)
    show_pods(node, namespace)


if __name__ == "__main__":
    main()


