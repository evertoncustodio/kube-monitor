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



