import argument
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
kubectl = Executor("kubectl")

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


