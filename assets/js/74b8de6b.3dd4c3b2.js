"use strict";(self.webpackChunkmare_ai=self.webpackChunkmare_ai||[]).push([[484],{3905:(e,t,a)=>{a.d(t,{Zo:()=>c,kt:()=>u});var n=a(7294);function r(e,t,a){return t in e?Object.defineProperty(e,t,{value:a,enumerable:!0,configurable:!0,writable:!0}):e[t]=a,e}function o(e,t){var a=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);t&&(n=n.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),a.push.apply(a,n)}return a}function l(e){for(var t=1;t<arguments.length;t++){var a=null!=arguments[t]?arguments[t]:{};t%2?o(Object(a),!0).forEach((function(t){r(e,t,a[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(a)):o(Object(a)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(a,t))}))}return e}function i(e,t){if(null==e)return{};var a,n,r=function(e,t){if(null==e)return{};var a,n,r={},o=Object.keys(e);for(n=0;n<o.length;n++)a=o[n],t.indexOf(a)>=0||(r[a]=e[a]);return r}(e,t);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(e);for(n=0;n<o.length;n++)a=o[n],t.indexOf(a)>=0||Object.prototype.propertyIsEnumerable.call(e,a)&&(r[a]=e[a])}return r}var p=n.createContext({}),s=function(e){var t=n.useContext(p),a=t;return e&&(a="function"==typeof e?e(t):l(l({},t),e)),a},c=function(e){var t=s(e.components);return n.createElement(p.Provider,{value:t},e.children)},d={inlineCode:"code",wrapper:function(e){var t=e.children;return n.createElement(n.Fragment,{},t)}},m=n.forwardRef((function(e,t){var a=e.components,r=e.mdxType,o=e.originalType,p=e.parentName,c=i(e,["components","mdxType","originalType","parentName"]),m=s(a),u=r,k=m["".concat(p,".").concat(u)]||m[u]||d[u]||o;return a?n.createElement(k,l(l({ref:t},c),{},{components:a})):n.createElement(k,l({ref:t},c))}));function u(e,t){var a=arguments,r=t&&t.mdxType;if("string"==typeof e||r){var o=a.length,l=new Array(o);l[0]=m;var i={};for(var p in t)hasOwnProperty.call(t,p)&&(i[p]=t[p]);i.originalType=e,i.mdxType="string"==typeof e?e:r,l[1]=i;for(var s=2;s<o;s++)l[s]=a[s];return n.createElement.apply(null,l)}return n.createElement.apply(null,a)}m.displayName="MDXCreateElement"},2167:(e,t,a)=>{a.r(t),a.d(t,{assets:()=>p,contentTitle:()=>l,default:()=>d,frontMatter:()=>o,metadata:()=>i,toc:()=>s});var n=a(7462),r=(a(7294),a(3905));const o={sidebar_position:2},l="Control Plane",i={unversionedId:"getting-started/deployment/control-plane",id:"getting-started/deployment/control-plane",title:"Control Plane",description:"Control plane is responsible for orchestrating communication between nodes in the cluster.",source:"@site/docs/getting-started/deployment/control-plane.md",sourceDirName:"getting-started/deployment",slug:"/getting-started/deployment/control-plane",permalink:"/docs/getting-started/deployment/control-plane",draft:!1,editUrl:"https://github.com/gregbugaj/marie-ai/tree/develop/docs/docs/getting-started/deployment/control-plane.md",tags:[],version:"current",sidebarPosition:2,frontMatter:{sidebar_position:2},sidebar:"tutorialSidebar",previous:{title:"Docker - Single node",permalink:"/docs/getting-started/deployment/docker"},next:{title:"Observability",permalink:"/docs/getting-started/deployment/observability"}},p={},s=[{value:"Docker Compose",id:"docker-compose",level:2},{value:"User and permission setup",id:"user-and-permission-setup",level:3},{value:"Networking setup",id:"networking-setup",level:3},{value:"Starting and stopping",id:"starting-and-stopping",level:3},{value:"Kubernetes",id:"kubernetes",level:2},{value:"Services",id:"services",level:2},{value:"Logging queries",id:"logging-queries",level:2}],c={toc:s};function d(e){let{components:t,...a}=e;return(0,r.kt)("wrapper",(0,n.Z)({},c,a,{components:t,mdxType:"MDXLayout"}),(0,r.kt)("h1",{id:"control-plane"},"Control Plane"),(0,r.kt)("p",null,"Control plane is responsible for orchestrating communication between nodes in the cluster."),(0,r.kt)("h2",{id:"docker-compose"},"Docker Compose"),(0,r.kt)("p",null,"Quickest way to bootstrap control plane is via ",(0,r.kt)("inlineCode",{parentName:"p"},"docker compose"),".\nInstall new version of ",(0,r.kt)("a",{parentName:"p",href:"https://docs.docker.com/compose/install/"},"docker compose cli plugin")),(0,r.kt)("h3",{id:"user-and-permission-setup"},"User and permission setup"),(0,r.kt)("p",null,"The container is setup with ",(0,r.kt)("inlineCode",{parentName:"p"},"app-svc")," account so for that we will setup same account in the host system."),(0,r.kt)("p",null,"Setting up user, for more info visit ",(0,r.kt)("a",{parentName:"p",href:"https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user"},"Manage Docker as a non-root user")),(0,r.kt)("p",null,(0,r.kt)("inlineCode",{parentName:"p"},"uid")," is a number associated with a user account and ",(0,r.kt)("inlineCode",{parentName:"p"},"gid")," is a number associated with a group\nAssigned ID that are mapped from within the container to outside world."),(0,r.kt)("p",null,(0,r.kt)("inlineCode",{parentName:"p"},"431")," : UID\n",(0,r.kt)("inlineCode",{parentName:"p"},"433")," : GUI"),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-shell"},"sudo groupadd -r app-svc -g 433\nsudo useradd -u 431 --comment 'app-svc' --create-home app-svc --shell /bin/bash\nsudo usermod -aG docker app-svc\n")),(0,r.kt)("p",null,"You can verify the user\u2019s UID, using the id command:"),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-shell"},"$ id -u app-svc\n")),(0,r.kt)("p",null,"Directory structure, this is more of a convention than requirement."),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-sh"},"sudo mkdir -p /opt/containers/apps/marie-ai\nsudo mkdir -p /opt/containers/config/marie-ai\n")),(0,r.kt)("p",null,"Change permissions to ",(0,r.kt)("inlineCode",{parentName:"p"},"app")," and ",(0,r.kt)("inlineCode",{parentName:"p"},"config")),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-shell"},"cd /opt/containers\nsudo chown app-svc:app-svc apps/ -R\nsudo chown app-svc:app-svc config/ -R\n")),(0,r.kt)("p",null,"Now that we have our directory and permissions setup we can move on and setup the container.\nThe easiest way to manage container is by checking out the ",(0,r.kt)("a",{parentName:"p",href:"https://github.com/gregbugaj/marie-ai.git"},"Marie-AI project")),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-shell"},"sudo su app-svc\ngit clone https://github.com/gregbugaj/marie-ai.git\n")),(0,r.kt)("h3",{id:"networking-setup"},"Networking setup"),(0,r.kt)("p",null,"The configuration uses custom bridge networks called ",(0,r.kt)("inlineCode",{parentName:"p"},"public")," which we will create first."),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-shell"},"docker network create --driver=bridge public\n\n# If you receive following error, enable IPv4 forwarding\n# WARNING: IPv4 forwarding is disabled. Networking will not work.\nsysctl net.ipv4.conf.all.forwarding=1\n")),(0,r.kt)("h3",{id:"starting-and-stopping"},"Starting and stopping"),(0,r.kt)("p",null,"Starting and stopping specific services"),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-shell"},"docker compose down \\ \ndocker compose -f docker-compose.yml -f docker-compose.storage.yml \\\n--project-directory . up loki consul-server grafana prometheus traefik whoami  --build  --remove-orphans\n")),(0,r.kt)("h2",{id:"kubernetes"},"Kubernetes"),(0,r.kt)("p",null,(0,r.kt)("a",{parentName:"p",href:"https://kubernetes.io/docs/tasks/configure-pod-container/translate-compose-kubernetes/"},"Translate a Docker Compose File to Kubernetes Resources")),(0,r.kt)("h2",{id:"services"},"Services"),(0,r.kt)("p",null,"There are number of services that made up control plane. "),(0,r.kt)("admonition",{title:"SSH Port Forwarding",type:"info"},(0,r.kt)("p",{parentName:"admonition"},"Some admin service can only be accesses via ",(0,r.kt)("inlineCode",{parentName:"p"},"localhost")," host. We will use SSH forwarding to allow this from our local machine to control-plane."),(0,r.kt)("p",{parentName:"admonition"},"Replace ",(0,r.kt)("inlineCode",{parentName:"p"},"ops-001")," with the name of the control plane server."),(0,r.kt)("pre",{parentName:"admonition"},(0,r.kt)("code",{parentName:"pre",className:"language-shell"},"ssh -vnT -N -L 8500:ops-001:8500 -L 5000:ops-001:5000  -L 7777:ops-001:7777 -L 9090:ops-001:9090 -L 3000:ops-001:3000 -L 3100:ops-001:3100 -L 9093:ops-001:9093 ops-001\n")),(0,r.kt)("p",{parentName:"admonition"},(0,r.kt)("a",{parentName:"p",href:"https://explainshell.com/explain?cmd=ssh+-N+-L+8500%3Aops-001%3A8500+-L+7777%3Aops-001%3A7777+-L+9090%3Aops-001%3A9090+-L+3000%3Aops-001%3A3000+ops-001"},"Explain"))),(0,r.kt)("table",null,(0,r.kt)("thead",{parentName:"table"},(0,r.kt)("tr",{parentName:"thead"},(0,r.kt)("th",{parentName:"tr",align:null},"Service"),(0,r.kt)("th",{parentName:"tr",align:null},"Endpoint"),(0,r.kt)("th",{parentName:"tr",align:null},"Description"))),(0,r.kt)("tbody",{parentName:"table"},(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"Consul"),(0,r.kt)("td",{parentName:"tr",align:null},"http://localhost:8500/ui/"),(0,r.kt)("td",{parentName:"tr",align:null},"Consul is a distributed, highly available, and data center aware solution to connect and configure applications across dynamic, distributed infrastructure.")),(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"Traefik"),(0,r.kt)("td",{parentName:"tr",align:null},(0,r.kt)("a",{parentName:"td",href:"http://traefik.localhost:7777/dashboard/#/"},"http://traefik.localhost:7777/dashboard/#/")," ",(0,r.kt)("a",{parentName:"td",href:"http://traefik.localhost:7777/metrics"},"http://traefik.localhost:7777/metrics")),(0,r.kt)("td",{parentName:"tr",align:null},"Traefik is a modern HTTP reverse proxy and load balancer that makes deploying microservices easy.")),(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"Grafana"),(0,r.kt)("td",{parentName:"tr",align:null},"http://localhost:3000/"),(0,r.kt)("td",{parentName:"tr",align:null},"The open and composable observability and data visualization platform.")),(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"Prometheus"),(0,r.kt)("td",{parentName:"tr",align:null},"http://localhost:9090/"),(0,r.kt)("td",{parentName:"tr",align:null},"The Prometheus monitoring system and time series database.")),(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"Alertmanager"),(0,r.kt)("td",{parentName:"tr",align:null},"http://localhost:9093/"),(0,r.kt)("td",{parentName:"tr",align:null},"The Alertmanager handles alerts sent by client applications such as the Prometheus server.")),(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"Loki"),(0,r.kt)("td",{parentName:"tr",align:null},"http://localhost:3100/ready"),(0,r.kt)("td",{parentName:"tr",align:null},"Loki is a horizontally scalable, highly available, multi-tenant log aggregation system inspired by Prometheus")))),(0,r.kt)("p",null,"Traefik - Service endpoints can be changed in the configs but by default they are as follow: "),(0,r.kt)("table",null,(0,r.kt)("thead",{parentName:"table"},(0,r.kt)("tr",{parentName:"thead"},(0,r.kt)("th",{parentName:"tr",align:null},"Traefik - Service"),(0,r.kt)("th",{parentName:"tr",align:null},"Endpoint"))),(0,r.kt)("tbody",{parentName:"table"},(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"Dashboard"),(0,r.kt)("td",{parentName:"tr",align:null},(0,r.kt)("a",{parentName:"td",href:"http://traefik.localhost:7777/dashboard/#/"},"http://traefik.localhost:7777/dashboard/#/"))),(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"traefik"),(0,r.kt)("td",{parentName:"tr",align:null},(0,r.kt)("a",{parentName:"td",href:"http://traefik.localhost:7777/"},"http://traefik.localhost:7777/"))),(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"traefik-debug"),(0,r.kt)("td",{parentName:"tr",align:null},(0,r.kt)("a",{parentName:"td",href:"http://traefik.localhost:7000/"},"http://traefik.localhost:7000/"))),(0,r.kt)("tr",{parentName:"tbody"},(0,r.kt)("td",{parentName:"tr",align:null},"Service endpoint"),(0,r.kt)("td",{parentName:"tr",align:null},(0,r.kt)("a",{parentName:"td",href:"http://traefik.localhost:5000/"},"http://traefik.localhost:5000/"))))),(0,r.kt)("admonition",{title:"Grafana Data Sources / Loki",type:"warning"},(0,r.kt)("p",{parentName:"admonition"},"When configuring Grafana Loki Datasource make sure to use the public ",(0,r.kt)("inlineCode",{parentName:"p"},"IP")," or ",(0,r.kt)("inlineCode",{parentName:"p"},"hostname")," and not loopback ip(127.0.0.1/localhost)\nin the HTTP URL field."),(0,r.kt)("p",{parentName:"admonition"},"Example\n",(0,r.kt)("inlineCode",{parentName:"p"},"http://ops-001:3100"))),(0,r.kt)("h2",{id:"logging-queries"},"Logging queries"),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-sql"},'{job="marie-ai"} |= `` | json | line_format `{{.msg}}`\n')),(0,r.kt)("pre",null,(0,r.kt)("code",{parentName:"pre",className:"language-sql"},'{job="marie-ai"} |= `` | json | levelname = `ERROR` | line_format `{{.msg}}`\n')))}d.isMDXComponent=!0}}]);