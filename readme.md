# Kube-Monitor

A simple kubernetes node and pod monitor written in Python

## How it works?

It uses kubectl to get information about the nodes and pos in a kubernetes cluster. 
It also uses metrics-server to get information about resource utilization, so it must be present in the cluster. 


