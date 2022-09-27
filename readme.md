# Kube-Monitor

A simple kubernetes node and pod monitor written in Python

## How it works?

It uses kubectl to get information about the nodes and pos in a kubernetes cluster. 
It also uses metrics-server to get information about resource utilization, so it must be present in the cluster. 

## Usage

All Nodes and Pods:
````bash
python kube-monitor.py
````

All Pods from a single Node:
````bash
python kube-monitor.py --node=my-node1
````

All Pods from a namespace:
````bash
python kube-monitor.py --namespace=my-namespace
````

All Pods from a Node and Namespace:
````bash
python kube-monitor.py --node=my-node1 --namespace=my-namespace
````

