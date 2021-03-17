# restricted-k8s-ns
How to Create Restricted Namespace K8s

Setting Python environment and Running Script to create NameSpace

```
python3
pip install kubernetes
edit admin kubeconfig location in script
python3 namespace.py --namespace=test-ns --primary=user1 --secondary=user2 --org=it-apps --teammail=teamdl --units=4
```
