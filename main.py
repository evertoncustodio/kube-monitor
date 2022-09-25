from pyexecutor import Executor
from kubernetes_types import Resource, Container, Pod, Node
from tabulate import tabulate
import json


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
    pods = json.loads(kubectl.run("get pod -o json"))
    for item in pods["items"]:
        metadata = item["metadata"]
        name = metadata["name"]
        namespace = metadata["namespace"]
        spec = item["spec"]
        node_name = spec["nodeName"]

        pod = Pod(namespace, name, node_name)
        pod_dict[pod.id] = pod

        node = node_dict[node_name]
        node.add_pod(pod)

        top = json.loads(kubectl.run(f"get --raw /apis/metrics.k8s.io/v1beta1/namespaces/{namespace}/pods/{name}"))

        for container_json in spec["containers"]:
            container_name = container_json["name"]

            resources = container_json["resources"]
            limits = resources["limits"]
            cpu_limits = limits["cpu"]
            memory_limits = limits["memory"]

            requests = resources["requests"]
            cpu_requests = requests["cpu"]
            memory_requests = requests["memory"]

            requests = Resource(cpu_requests, memory_requests)
            limits = Resource(cpu_limits, memory_limits)
            container = Container(name, requests, limits)
            pod.add_container(container)


def show_nodes():
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


def show_pods():
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

        line = [
            pod.node_name,
            pod.namespace,
            pod.name,
            pod.get_cpu_utilization(),
            pod.get_resource_requests().get_cpu(),
            pod.get_resource_limits().get_cpu(),
            pod.get_memory_utilization(),
            pod.get_resource_requests().get_memory(),
            pod.get_resource_limits().get_memory()
        ]
        table.append(line)

    print(tabulate(table, headers))


kubectl = Executor("kubectl")

node_dict = {}
pod_dict = {}

load_nodes()
load_pods()

show_pods()


