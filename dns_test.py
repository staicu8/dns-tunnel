from dnslib import DNSRecord, RR, QTYPE, TXT, A
import socket

IP_SERVER = "161.35.207.251"
ZONE = "tunel.retele.me."

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 53))

print("DNS server pornit pe portul 53")

while True:
    data, addr = sock.recvfrom(512)

    request = DNSRecord.parse(data)
    qname = str(request.q.qname)
    qtype = QTYPE[request.q.qtype]

    print(addr, qname, qtype)

    reply = request.reply()

    if qname.endswith(ZONE):
        if qtype == "TXT":
            reply.add_answer(
                RR(qname, QTYPE.TXT, rdata=TXT("merge"), ttl=30)
            )

        elif qtype == "A":
            reply.add_answer(
                RR(qname, QTYPE.A, rdata=A(IP_SERVER), ttl=30)
            )

    sock.sendto(reply.pack(), addr)
