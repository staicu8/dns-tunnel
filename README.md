# DNS Tunnel pentru transfer de fișiere

Demonstrație educațională de transfer de fișiere prin răspunsuri DNS TXT. Clientul cere metadatele și bucățile unui fișier, reia transferurile întrerupte și verifică rezultatul cu MD5.

## Componente

- `tunel_server.py` implementează serverul DNS autoritativ pentru zonă și servește fișierele din `files/`.
- `tunel_client.py` solicită fișierul în bucăți, are retry și păstrează `.part`/`.state` pentru reluare.
- `dns_test.py` este un server minimal folosit la testare.

## Cerințe

```bash
pip install -r requirements.txt
```

Ai nevoie de un server autorizat să asculte pe UDP/53 și de o zonă DNS delegată către el. Înainte de rulare, configurează `ZONA` și `IP_SERVER` din server pentru infrastructura ta.

```bash
# pe server
python tunel_server.py

# pe client
python tunel_client.py test.txt <adresa-resolverului>
```

Folosește acest cod numai într-un mediu controlat sau pentru infrastructura pe care o administrezi. Fișierele private și descărcările parțiale sunt ignorate de Git.
