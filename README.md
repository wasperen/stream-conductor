# stream-conductor
## synopsis
This service presents a flexible stream-proxy solution.
It enables the user to assign ports at the host where the service lives and have these being
transparantly proxied to a backend service.

### use case
You have a service running at a backend server; for example a _memcache_ service at `port 2000` on address `10.1.0.1`.
You cannot expose this port to the outside world, but still want it to be reachable.
But you do have an edge node that has an address that is accessible from the outside world, say at `85.12.23.34`.

Running this stream-conductor at that edge node gives you the ability to quickly assign a port at this external address
and have the stream-conductor reverse proxy all traffic to your backend service.

A simple `GET /createstream/9000/mybackend:2000` request will create a stream reverse proxy at `85.12.23.34:9000` to
the service at `mybackend:2000`.
From that point onwards, any requests at `85.12.23.34:9000` will be proxied to `mybackend:2000` and any application
using `85.12.23.34:9000` would not know better.

## interface
The service uses a REST API that has the following options:

*TODO*