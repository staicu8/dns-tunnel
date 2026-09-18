from dnslib import DNSRecord, RR, QTYPE, TXT, A, NS, RCODE
import socket
import os
import math
import hashlib
import base64


IP_SERVER = "161.35.207.251"
ZONA = "tunel.retele.me."
DIRECTOR_FISIERE = "files"
MARIME_BUCATA = 120


def md5_fisier(cale):
    hash_md5 = hashlib.md5()

    with open(cale, "rb") as fisier:
        while True:
            date = fisier.read(4096)

            if not date:
                break

            hash_md5.update(date)

    return hash_md5.hexdigest()


def nume_fisier_sigur(nume):
    nume = os.path.basename(nume)

    if nume == "":
        return None

    return nume


def adauga_txt(raspuns, qname, text):
    raspuns.add_answer(
        RR(
            qname,
            QTYPE.TXT,
            rdata=TXT(text),
            ttl=0
        )
    )


def raspunde_meta(raspuns, qname, nume):
    nume = nume_fisier_sigur(nume)

    if nume is None:
        adauga_txt(raspuns, qname, "ERR|nume invalid")
        return

    cale = os.path.join(DIRECTOR_FISIERE, nume)

    if not os.path.exists(cale):
        adauga_txt(raspuns, qname, "ERR|fisier inexistent")
        return

    marime = os.path.getsize(cale)
    bucati = math.ceil(marime / MARIME_BUCATA)
    md5 = md5_fisier(cale)

    mesaj = "META|{}|{}|{}|{}".format(marime, bucati, md5, MARIME_BUCATA)
    adauga_txt(raspuns, qname, mesaj)


def raspunde_bucata(raspuns, qname, index_text, nume):
    nume = nume_fisier_sigur(nume)

    if nume is None:
        adauga_txt(raspuns, qname, "ERR|nume invalid")
        return

    try:
        index = int(index_text)
    except:
        adauga_txt(raspuns, qname, "ERR|index invalid")
        return

    cale = os.path.join(DIRECTOR_FISIERE, nume)

    if not os.path.exists(cale):
        adauga_txt(raspuns, qname, "ERR|fisier inexistent")
        return

    with open(cale, "rb") as fisier:
        fisier.seek(index * MARIME_BUCATA)
        bucata = fisier.read(MARIME_BUCATA)

    if bucata == b"":
        adauga_txt(raspuns, qname, "ERR|index prea mare")
        return

    bucata_codata = base64.b64encode(bucata).decode()
    mesaj = "DATA|{}|{}".format(index, bucata_codata)

    adauga_txt(raspuns, qname, mesaj)


def proceseaza_cerere(date):
    cerere = DNSRecord.parse(date)
    qname = str(cerere.q.qname)
    qname_mic = qname.lower()
    qtype = QTYPE[cerere.q.qtype]

    raspuns = cerere.reply()

    print(qname, qtype)

    if qname_mic == ZONA and qtype == "NS":
        raspuns.add_answer(
            RR(
                qname,
                QTYPE.NS,
                rdata=NS("ns1.retele.me."),
                ttl=30
            )
        )
        return raspuns

    if qtype == "A":
        raspuns.add_answer(
            RR(
                qname,
                QTYPE.A,
                rdata=A(IP_SERVER),
                ttl=30
            )
        )
        return raspuns

    if not qname_mic.endswith(ZONA):
        raspuns.header.rcode = RCODE.NXDOMAIN
        return raspuns

    if qtype != "TXT":
        return raspuns

    prefix = qname_mic[:-len(ZONA)].strip(".")
    parti = prefix.split(".")

    if len(parti) < 2:
        adauga_txt(raspuns, qname, "ERR|cerere incompleta")
        return raspuns

    comanda = parti[0]

    if comanda == "meta":
        nume = ".".join(parti[1:])
        raspunde_meta(raspuns, qname, nume)

    elif comanda == "chunk" and len(parti) >= 3:
        index_text = parti[1]
        nume = ".".join(parti[2:])
        raspunde_bucata(raspuns, qname, index_text, nume)

    else:
        adauga_txt(raspuns, qname, "ERR|comanda necunoscuta")

    return raspuns


def main():
    socket_dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_dns.bind(("0.0.0.0", 53))

    print("DNS tunnel pornit pe UDP 53")
    print("Zona:", ZONA)
    print("Fisiere:", DIRECTOR_FISIERE)

    while True:
        date, adresa = socket_dns.recvfrom(512)

        try:
            raspuns = proceseaza_cerere(date)
            socket_dns.sendto(raspuns.pack(), adresa)
        except Exception as eroare:
            print("Eroare:", eroare)


if __name__ == "__main__":
    main()
