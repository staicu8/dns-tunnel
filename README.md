# DNS Tunnel

## What it is and the problem it solves

This project transfers a file through DNS TXT responses. The client requests metadata and numbered file chunks, retries failed requests, stores progress locally, and validates the completed transfer with MD5. This shows how a reliable file transfer layer can be built on top of DNS and UDP.

## Tech stack

- Python 3
- dnslib for DNS message construction and parsing
- UDP sockets for DNS transport
- Base64 for chunk encoding
- JSON state files and MD5 integrity checks for resumable downloads

## Running it

Install the dependency, configure `ZONA` and `IP_SERVER` in `tunel_server.py` for your DNS setup, then start the server and client.

```bash
cd tunel_dns
pip install -r requirements.txt

# server
python tunel_server.py

# client
python tunel_client.py test.txt <resolver-ip>
```

The server reads files from `files/`; the client writes incomplete downloads as `.part` and `.state` files before renaming a verified transfer.
