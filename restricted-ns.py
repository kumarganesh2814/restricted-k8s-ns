import yaml
from kubernetes import client, config
import base64
import sys,getopt
 
k8sconfig='/kubeconfig.yaml'
 
class Tkg():
    namespace_payload = {
        "apiVersion":"v1",
        "kind":"Namespace",
        "metadata":{
            "name":"t",
            "labels":{
                "PrimaryOwner":"",
                "SecondaryOwner":"",
                "Org":"",
                "TeamMail":""
        }
        },
        "spec":{},
        "status":{}
    }
    serviceaccount_payload = {
        "apiVersion": "v1",
        "kind":"ServiceAccount",
        "metadata":{
            "name": "NAMESPACEVAR-User",
            "namespace": "NAMESPACEVAR"
        }
    }
    memlimit_payload = {
        "apiVersion": "v1",
        "kind": "LimitRange",
        "metadata": {
            "name": "mem-limit-range-tkg-NAMESPACEVAR"
        },
        "spec": {
            "limits": [
                {
                    "default": {
                        "memory": "512Mi"
                    },
                    "defaultRequest": {
                        "memory": "256Mi"
                    },
                    "type": "Container"
                }
            ]
        }
    }
    cpulimit_payload = {
      "apiVersion": "v1",
      "kind": "LimitRange",
      "metadata": {
        "name": "cpu-limit-range-tkg-NAMESPACEVAR"
      },
      "spec": {
        "limits": [
          {
            "default": {
              "cpu": "200m"
            },
            "defaultRequest": {
              "cpu": "25m"
            },
            "type": "Container"
          }
        ]
      }
    }
    resourceQuota_payload = {
        "apiVersion": "v1",
        "kind": "ResourceQuota",
        "metadata": {
            "name": "NAMESPACEVAR-quota",
            "namespace": "NAMESPACEVAR"
        },
        "spec": {
            "hard": {
                "requests.cpu": "Units",
                "requests.memory": "RAMGi",
                "limits.cpu": "Units",
                "limits.memory": "RAMGi"
            }
        }
    }
    roleBinding_payload = {
      "apiVersion": "rbac.authorization.k8s.io/v1",
      "kind": "RoleBinding",
      "metadata": {
        "name": "NAMESPACEVAR-user-rb",
        "namespace": "NAMESPACEVAR"
      },
      "subjects": [
        {
          "kind": "ServiceAccount",
          "name": "NAMESPACEVAR-user",
          "namespace": "NAMESPACEVAR"
        }
      ],
      "roleRef": {
        "apiGroup": "rbac.authorization.k8s.io",
        "kind": "Role",
        "name": "NAMESPACEVAR-role"
      }
    }
    role_payload = {
      "kind": "Role",
      "apiVersion":"rbac.authorization.k8s.io/v1",
      "metadata": {
        "name": "NAMESPACEVAR-role",
        "namespace": "NAMESPACEVAR"
      },
      "rules": [
        {
          "apiGroups": [
            "",
            "metrics.k8s.io",
            "networking.k8s.io",
            "apps",
            "extensions",
            "autoscaling"
          ],
          "resources": [
            "pods/portforward",
            "pods/exec",
            "pods/log",
            "componentstatuses",
            "configmaps",
            "daemonsets",
            "deployments",
            "deployments/scale",
            "events",
            "endpoints",
            "horizontalpodautoscalers",
            "ingress",
            "ingresses",
            "jobs",
            "limitranges",
            "pods",
            "persistentvolumes",
            "persistentvolumeclaims",
            "replicasets",
            "replicationcontrollers",
            "secrets",
            "services",
            "statefulsets",
            "serviceaccounts",
            "top"
          ],
          "verbs": [
            "*"
          ]
        },
        {
          "apiGroups": [
            ""
          ],
          "resources": [
            "resourcequotas"
          ],
          "verbs": [
            "get",
            "watch",
            "list"
          ]
        },
        {
          "apiGroups": [
            "batch"
          ],
          "resources": [
            "jobs",
            "cronjobs"
          ],
          "verbs": [
            "*"
          ]
        },
        {
          "apiGroups": [
            ""
          ],
          "resources": [
            "namespaces"
          ],
          "verbs": [
            "describe",
            "get"
          ]
        }
      ]
}
    readrole_payload = {
      "kind": "Role",
      "apiVersion":"rbac.authorization.k8s.io/v1",
      "metadata": {
        "name": "NAMESPACEVAR-role",
        "namespace": "NAMESPACEVAR"
      },
      "rules": [
        {
          "apiGroups": [
            "",
            "metrics.k8s.io",
            "networking.k8s.io",
            "apps",
            "extensions",
            "autoscaling"
          ],
          "resources": [
            "pods/portforward",
            "pods/exec",
            "pods/log",
            "componentstatuses",
            "configmaps",
            "daemonsets",
            "deployments",
            "deployments/scale",
            "events",
            "endpoints",
            "horizontalpodautoscalers",
            "ingress",
            "ingresses",
            "jobs",
            "limitranges",
            "pods",
            "persistentvolumes",
            "persistentvolumeclaims",
            "replicasets",
            "replicationcontrollers",
            "secrets",
            "services",
            "statefulsets",
            "serviceaccounts",
            "top"
          ],
          "verbs": [
            "get",
            "watch",
            "list"
          ]
        },
 
      ]
}
    kubeconfig = {
      "apiVersion": "v1",
      "kind": "Config",
      "preferences": {},
      "clusters": [
        {
          "cluster": {
            "certificate-authority-data": "$certificate",
            "server": "$server_name"
          },
          "name": "$namespace-context"
        }
      ],
      "users": [
        {
          "name": "$namespace-user",
          "user": {
            "as-user-extra": {},
            "client-key-data": "$certificate",
            "token": "$token"
          }
        }
      ],
      "contexts": [
        {
          "context": {
            "cluster": "$namespace-context",
            "namespace": "$namespace",
            "user": "$namespace-user"
          },
          "name": "$namespace"
        }
      ],
      "current-context": "$namespace"
    }
 
    def __init__(self):
        self.config = config.load_kube_config(config_file=k8sconfig)
        self.v1 = client.CoreV1Api()
        self.v2 = client.RbacAuthorizationV1Api()
        self.v3 = client.AppsV1Api()
        self.custom = client.CustomObjectsApi()
 
    def read_adminKubeconfig(self):
        with open(file=k8sconfig, mode='r') as file:
            kube = yaml.full_load(file)
            return kube
 
    def create_ns(self,namespace,primary,secondary,org,teammail,units):
        self.namespace_payload['metadata']['name'] = namespace
        self.namespace_payload['metadata']['labels']['PrimaryOwner'] = primary
        self.namespace_payload['metadata']['labels']['SecondaryOwner'] = secondary
        self.namespace_payload['metadata']['labels']['Org'] = org
        self.namespace_payload['metadata']['labels']['TeamMail'] = teammail
        self.serviceaccount_payload['metadata']['name'] = namespace+'-user'
        self.serviceaccount_payload['metadata']['namespace'] = namespace
        self.memlimit_payload['metadata']['name'] = 'mem-limit-range-tkg-'+namespace
        self.cpulimit_payload['metadata']['name'] = 'cpu-limit-range-tkg-'+namespace
        self.resourceQuota_payload['metadata']['name'] = namespace+'-quota'
        self.resourceQuota_payload['metadata']['namespace'] = namespace
        self.resourceQuota_payload['spec']['hard']['requests.cpu'] = str(units)
        self.resourceQuota_payload['spec']['hard']['requests.memory'] = str(units*2)
        self.resourceQuota_payload['spec']['hard']['limits.cpu'] = str(units)
        self.resourceQuota_payload['spec']['hard']['limits.memory'] = str(units*2)
        self.roleBinding_payload['metadata']['name'] = namespace+'-user-rb'
        self.roleBinding_payload['subjects'][0]['name'] = namespace+'-user'
        self.roleBinding_payload['metadata']['namespace'] = namespace
        self.roleBinding_payload['subjects'][0]['namespace'] = namespace
        self.roleBinding_payload['roleRef']['name'] = namespace+'-role'
        self.role_payload['metadata']['name'] = namespace+'-role'
        self.role_payload['metadata']['namespace'] = namespace
        self.v1.create_namespace(self.namespace_payload)
        self.v1.create_namespaced_service_account(namespace,self.serviceaccount_payload)
        self.v1.create_namespaced_limit_range(namespace, self.cpulimit_payload)
        self.v1.create_namespaced_limit_range(namespace,self.memlimit_payload)
        self.v1.create_namespaced_resource_quota(namespace,self.resourceQuota_payload)
        self.v2.create_namespaced_role(namespace,self.role_payload)
        self.v2.create_namespaced_role_binding(namespace,self.roleBinding_payload)
        return "Role and Namespace Created"
 
 
    def get_ns_kubeconfig(self,namespace):
        read_tokenname = self.v1.read_namespaced_service_account(name=namespace+'-user',namespace=namespace).secrets[0].name
        read_token = self.v1.read_namespaced_secret(read_tokenname,namespace)
        cert=read_token.data['ca.crt']
        token = read_token.data['token']
        token = base64.b64decode(token.encode("ascii")).decode('ascii')
        adminkubeconfig = self.read_adminKubeconfig()
        self.kubeconfig['clusters'][0]['cluster']['certificate-authority-data'] = cert
        self.kubeconfig['clusters'][0]['cluster']['server'] = adminkubeconfig['clusters'][0]['cluster']['server']
        self.kubeconfig['clusters'][0]['name'] = namespace+'-context'
        self.kubeconfig['users'][0]['user']['client-key-data'] = cert
        self.kubeconfig['users'][0]['user']['token'] = token
        self.kubeconfig['users'][0]['name'] = namespace+'-user'
        self.kubeconfig['contexts'][0]['context']['cluster'] = namespace+'-context'
        self.kubeconfig['contexts'][0]['context']['namespace'] = namespace
        self.kubeconfig['contexts'][0]['name'] = namespace
        self.kubeconfig['contexts'][0]['context']['user'] = namespace+'-user'
        self.kubeconfig['current-context'] = namespace
 
        k_yaml = yaml.dump(self.kubeconfig,sort_keys=False)
        return k_yaml
 
  
 
def main(argv):
   namespace = ''
   primary = ''
   secondary = ''
   org = ''
   teammail = ''
   units = ''
   try:
      opts, args = getopt.getopt(argv,"hn:p:s:o:t:u",["namespace=","primary=","secondary=","org=","teammail=","units="])
   except getopt.GetoptError:
      print('namespace.py -n <namespace> -p <primary> -s <secondary> -o <org> -t <teammail> -u <units>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('namespace.py -n <namespace> -p <primary> -s <secondary> -o <org> -t <teammail> -u <units>')
         sys.exit()
      elif opt in ("-n", "--namespace"):
         namespace = arg
      elif opt in ("-p", "--primary"):
         primary = arg
      elif opt in ("-s", "--secondary"):
         secondary = arg
      elif opt in ("-o", "--org"):
         org = arg
      elif opt in ("-t", "--teammail"):
         teammail = arg
      elif opt in ("-u", "--units"):
         units = arg     
    
   print(namespace,primary,secondary,org,teammail,units)
   print("==============================================")  
   print(Tkg().create_ns(namespace,primary,secondary,org,teammail,units))
   print("==============================================")
   print(Tkg().get_ns_kubeconfig(namespace))
 
if __name__ == "__main__":
   main(sys.argv[1:])
