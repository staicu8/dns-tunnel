from dnslib import DNSRecord, QTYPE
import socket
import sys
import os
import json
import time
import base64
import hashlib


ZONA = "tunel.retele.me"
DIRECTOR_DESCARCARI = "downloads"


def txt_din_raspuns(raspuns):
    for rr in raspuns.rr:
        if QTYPE[rr.rtype] == "TXT":
            parti = rr.rdata.data
            text = ""

            for parte in parti:
                if isinstance(parte, bytes):
                    text += parte.decode(errors="ignore")
                else:
                    text += str(parte)

            return text

    return None


def interogheaza_dns(nume, resolver):
    cerere = DNSRecord.question(nume, "TXT")

    socket_dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_dns.settimeout(3)
    socket_dns.sendto(cerere.pack(), (resolver, 53))

    date, _ = socket_dns.recvfrom(512)
    raspuns = DNSRecord.parse(date)

    return txt_din_raspuns(raspuns)


def interogheaza_cu_retry(nume, resolver):
    for incercare in range(5):
        try:
            raspuns = interogheaza_dns(nume, resolver)

            if raspuns is not None:
                return raspuns

        except Exception:
            pass

        time.sleep(1)

    return None


def md5_fisier(cale):
    hash_md5 = hashlib.md5()

    with open(cale, "rb") as fisier:
        while True:
            date = fisier.read(4096)

            if not date:
                break

            hash_md5.update(date)

    return hash_md5.hexdigest()


def citeste_meta(nume_fisier, resolver):
    qname = "meta.{}.{}".format(nume_fisier, ZONA)
    raspuns = interogheaza_cu_retry(qname, resolver)

    if raspuns is None:
        print("META lipsa")
        return None

    parti = raspuns.split("|")

    if len(parti) != 5 or parti[0] != "META":
        print("META invalid:", raspuns)
        return None

    return {
        "marime": int(parti[1]),
        "bucati": int(parti[2]),
        "md5": parti[3],
        "marime_bucata": int(parti[4])
    }


def descarca_bucata(nume_fisier, index, resolver):
    qname = "chunk.{}.{}.{}".format(index, nume_fisier, ZONA)
    raspuns = interogheaza_cu_retry(qname, resolver)

    if raspuns is None:
        return None

    parti = raspuns.split("|", 2)

    if len(parti) != 3:
        return None

    if parti[0] != "DATA":
        return None

    if int(parti[1]) != index:
        return None

    return base64.b64decode(parti[2].encode())


def main():
    if len(sys.argv) < 2:
        print("Utilizare:")
        print("python3 tunel_client.py test.txt")
        print("python3 tunel_client.py test.txt 161.35.207.251")
        return

    nume_fisier = sys.argv[1]

    if len(sys.argv) >= 3:
        resolver = sys.argv[2]
    else:
        resolver = "1.1.1.1"

    os.makedirs(DIRECTOR_DESCARCARI, exist_ok=True)

    meta = citeste_meta(nume_fisier, resolver)

    if meta is None:
        return

    cale_finala = os.path.join(DIRECTOR_DESCARCARI, nume_fisier)
    cale_partiala = cale_finala + ".part"
    cale_stare = cale_finala + ".state"

    start = 0

    if os.path.exists(cale_stare):
        with open(cale_stare, "r") as fisier:
            stare = json.load(fisier)

        if stare.get("md5") == meta["md5"]:
            start = stare.get("next_index", 0)

    elif os.path.exists(cale_partiala):
        start = os.path.getsize(cale_partiala) // meta["marime_bucata"]

    print("Fisier:", nume_fisier)
    print("Marime:", meta["marime"])
    print("Bucati:", meta["bucati"])
    print("MD5 asteptat:", meta["md5"])
    print("Resolver:", resolver)
    print("Start bucata:", start)

    mod = "ab" if start > 0 else "wb"

    with open(cale_partiala, mod) as fisier:
        for index in range(start, meta["bucati"]):
            bucata = descarca_bucata(nume_fisier, index, resolver)

            if bucata is None:
                print("Bucata lipsa:", index)
                return

            fisier.write(bucata)
            fisier.flush()

            with open(cale_stare, "w") as fisier_stare:
                json.dump(
                    {
                        "md5": meta["md5"],
                        "next_index": index + 1
                    },
                    fisier_stare
                )

            print("Bucata primita:", index)

    md5_obtinut = md5_fisier(cale_partiala)

    print("MD5 obtinut:", md5_obtinut)

    if md5_obtinut == meta["md5"]:
        os.rename(cale_partiala, cale_finala)

        if os.path.exists(cale_stare):
            os.remove(cale_stare)

        print("Transfer complet:", cale_finala)
    else:
        print("MD5 diferit:", cale_partiala)


if __name__ == "__main__":
    main()
