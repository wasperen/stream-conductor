# stream-conductor
## synopsis
This service presents a flexible stream proxy solution.
It enables the user to assign ports at the host where the service lives and have these being
transparantly proxied to a backend service.

This repository provides the service code (Python 3) as well as a Dockerfile to create the service as docker container.
A `docker compose` file is provided as a quick test and demo. It spins up the `stream-conductor` service and a 
backend ssh service (based on macropin/sshd) as a demo.

### use case
You have a service running at a backend server; for example a _memcache_ service at `port 2000` on address `10.1.0.1`.
You cannot expose this port to the outside world, but still want it to be reachable.
If you do have an edge node that has an address that is accessible from the outside world, say at `85.12.23.34`.

Running this stream-conductor at that edge node gives you the ability to quickly assign a port at this external address
and have the stream-conductor reverse proxy all traffic to your backend service.

A simple `GET /createstream/9000/mybackend:2000` request will create a stream reverse proxy at `85.12.23.34:9000` to
the service at `mybackend:2000`.
From that point onwards, any requests at `85.12.23.34:9000` will be proxied to `mybackend:2000` and any application
using `85.12.23.34:9000` would not know better.

## starting the serivce
The service uses the following environment variables:

| variable | default | description |
|----------|---------|-------------|
| STREAM_CONFIG_PATH | `/etc/nginx/stream.d/` | path to store the stream definition files |
| NGINX_BIN | `/usr/sbin/nginx` | path to the nginx binary |
| STREAM_PREFIX | `_conductor_` | prefix to the per-stream configuration files |
| PORT_RANGE | `9000-9009` | port range[^1] that is available through this service |
| BIND_ADDRESS | `0.0.0.0` (all) | addresses that the API will bind to |
| BIND_PORT | `5000` | port that the API will bind to |

[^1]: The Dockerfile exposes only port 5000 and 9000-9009. If you need other ports, you will need to create your own image.

## interface
The service uses a REST API that has the following options:

| function | example result | description |
|----------|----------------|-------------|
| status | `{ 'version':'0.1', 'range':'range(9000-9999)' }` | returns the current API version and range of available ports |
| getstreams | `[ { 'listen': 9000, 'proxy_pass': 'mybackend:22' } ]` | get a list of current stream definitions |
| createstream/`<port>`/`<backend>` | `{ 'result':'ok', 'errors':'...'}` | create a stream connecting a port `<port>` to a backend service `<backend>` |
| removestream/`<port>` | `{ 'result':'ok' }` | remove the stream that listens at port `<port>` |
| hasstream/`<port>` | `{ 'result':'false' }` | returns `true` if there is a stream created that listens at port `<port>` |
| getfreeport | `{ 'result':'ok', 'port':9010 }` | returns the first available port |

### examples
#### getting the status
```bash
$ curl localhost:5000/status
{"version": "0.1", "available_ports": "range(9000, 9009)"}
``` 

#### creating a stream
```bash
$ curl localhost:5000/createstream/9000/streamconductor_backendssh_1.streamconductor_default:22
{"errors": "[b'2017/06/05 09:27:22 [notice] 10#10: signal process started\\n']", "result": "ok"}
$ ssh localhost -p9000
The authenticity of host '[localhost]:9000 ([::1]:9000)' can't be established.
ECDSA key fingerprint is SHA256:am/KOV40B7/LUbBRb2V2DuwJYL9mPfqq2k2ClERFR6k.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '[localhost]:9000' (ECDSA) to the list of known hosts.
willem@localhost's password:
```
In this example, a stream is created, proxying port `9000` to the service at
`streamconductor_backendssh_1.streamconductor_default:22`. An `ssh` to that port is demonstrated to be proxied.

#### getting a list of streams
```bash
$ curl localhost:5000/getstreams
[{"proxy_pass": "localhost:4321", "listen": 1234}, 
{"proxy_pass": "streamconductor_backendssh_1.streamconductor_default:22", "listen": 9000}]
```
Here a list of all stream mappings is returned.

#### removing a stream
```bash
$ curl localhost:5000/removestream/9000
{"result": "ok", "errors": "[b'2017/06/05 09:34:11 [notice] 12#12: signal process started\\n']"}
```
This example removes the stream that listens to port `9000` from the proxy.


### background
The proxy service is backed by nginx (http://nginx.org/).
A simple python program is created to manage the stream definitions and reconfigure nginx.
The python program is exposed as REST API using Flask.

NB: There is absolutely no authorization or even authentication done!
