# Cerinte proiect - Mini Blockchain (C/C++ & Python)

Proiect educational: implementare minimala de blockchain, cu nucleul in C/C++,
stratul de retea/API in Python. Documentul descrie cerintele pe fiecare modul,
in ordinea logica de dezvoltare (Modulul 11 - UI - e tratat separat).

---

## Modulul 0 - Fundamente teoretice (hashing & blockchain)

**Domeniu:** criptografie aplicata, teorie

**Cerinte tehnice minime:**
- Intelegerea proprietatilor unei functii hash criptografice: determinism,
  efect de avalansa, ireversibilitate, rezistenta la coliziuni
- Cunoasterea structurii generale SHA-256 (blocuri de 512 biti, runde de
  comprimare, constante initiale)
- Intelegerea conceptului de "lant" - fiecare bloc contine hash-ul precedentului

**Directie:**
Nu produce cod. Rezultatul acestui modul e o baza teoretica solida, necesara
inainte de a scrie orice linie din nucleul C.

---

## Modulul 1 - Structura unui bloc

**Domeniu:** programare C/C++, structuri de date

**Cerinte tehnice minime:**
- Definirea unui `struct Block` cu minim: index, timestamp, hash-ul blocului
  anterior (`prev_hash`), date/tranzactii, `nonce`, hash propriu
- Alocare/dealocare corecta de memorie pentru campurile dinamice (ex. string-uri
  de hash, daca nu sunt de dimensiune fixa)
- Functie de afisare/debug a unui bloc

**Directie:**
Rezultatul e un bloc "gol" functional - poate fi creat, populat cu date, afisat,
dar inca fara hash calculat real si fara legatura cu alte blocuri.

---

## Modulul 2 - Hashing (SHA-256)

**Domeniu:** criptografie aplicata, integrare biblioteci externe

**Cerinte tehnice minime:**
- Intelegerea la nivel conceptual a algoritmului SHA-256 (padding, impartire
  in blocuri de 512 biti, rundele de comprimare, constantele initiale) - fara
  a fi nevoie de implementare proprie
- Folosirea unei biblioteci criptografice existente (ex. OpenSSL) pentru
  calculul efectiv al hash-ului in cod
- Functie wrapper care primeste un buffer de octeti si intoarce hash-ul pe
  256 biti (reprezentat, de regula, ca string hexazecimal de 64 caractere)
- Teste de verificare fata de valori hash cunoscute (test vectors oficiale)

**Directie:**
Rezultatul e o functie de hashing integrata in proiect, bazata pe o biblioteca
externa consacrata, pe care Modulul 1 si cele urmatoare o vor folosi direct.
Scopul e intelegerea corecta a algoritmului, nu reimplementarea lui de la zero.

---

## Modulul 3 - Linking si validare lant

**Domeniu:** structuri de date (liste inlantuite), integritate a datelor

**Cerinte tehnice minime:**
- Structura de tip lista/array de blocuri, unde fiecare bloc retine hash-ul
  celui anterior
- Functie `is_chain_valid()` care parcurge intregul lant si verifica pentru
  fiecare bloc: hash-ul calculat corespunde cu cel stocat, si corespunde cu
  referinta din blocul urmator
- Functie de adaugare a unui bloc nou, validat, la finalul lantului

**Directie:**
Rezultatul e un lant functional care poate detecta orice modificare a
istoricului - testul minim de acceptare: modifici manual un camp dintr-un
bloc vechi si `is_chain_valid()` trebuie sa intoarca fals.

---

## Modulul 4 - Mining (Proof of Work)

**Domeniu:** algoritmi, performanta, brute-force computational

**Cerinte tehnice minime:**
- Camp de dificultate (target) - ex. hash-ul trebuie sa inceapa cu N zerouri
- Bucla de mining: variaza `nonce`, recalculeaza hash-ul, verifica fata de
  target, pana gaseste o solutie valida
- Masurare a timpului de mining, in functie de dificultate

**Directie:**
Rezultatul e un miner functional care produce blocuri valide conform
dificultatii impuse. De aici rezulta si un experiment concret: cresterea
dificultatii (mai multe zerouri cerute) trebuie sa creasca exponential timpul
de mining.

---

## Modulul 5 - Tranzactii si Merkle tree

**Domeniu:** structuri de date (arbori binari), criptografie aplicata

**Cerinte tehnice minime:**
- Structura de tranzactie (minim: expeditor, destinatar, suma)
- Implementare de Merkle tree pornind de la o lista de tranzactii
  (hash-uri combinate perechi, pana la un singur hash radacina)
- Functie de generare a unui proof-of-inclusion (dovada ca o tranzactie
  anume face parte dintr-un bloc, fara a expune toate celelalte tranzactii)

**Directie:**
Blocul trece de la un camp `data` simplu la o lista reala de tranzactii,
identificate printr-un singur hash radacina (Merkle root) stocat in header-ul
blocului.

---

## Modulul 6 - Persistenta

**Domeniu:** serializare, I/O pe disk

**Cerinte tehnice minime:**
- Format de serializare pentru blocuri/lant (JSON simplu sau format binar
  propriu)
- Functie de salvare a intregului lant pe disk
- Functie de incarcare a lantului de pe disk, cu validare completa la load

**Directie:**
Lantul supravietuieste repornirii aplicatiei - rezultatul e testabil oprind
si repornind programul si verificand ca lantul e identic si valid.

---

## Modulul 7 - Retea P2P

**Domeniu:** networking, programare Python, sisteme distribuite

**Cerinte tehnice minime:**
- Fiecare nod ruleaza ca proces separat, comunica prin sockets (TCP)
- Mecanism de sincronizare la pornire (un nod nou cere lantul de la peers)
- Propagare (broadcast) a blocurilor noi minate catre ceilalti peers

**Directie:**
Rezultatul e o retea functionala de minim 3 noduri, unde un bloc minat pe un
nod ajunge, prin propagare, la toate celelalte, iar un nod oprit si repornit
se resincronizeaza corect.

---

## Modulul 8 - Consens si fork resolution

**Domeniu:** sisteme distribuite, algoritmi de consens

**Cerinte tehnice minime:**
- Detectarea unui fork (doi mineri gasesc blocuri valide, la aceeasi inaltime,
  aproape simultan)
- Implementarea regulii "cel mai lung lant castiga" (longest chain rule)
- Realiniere a nodurilor cu lantul minoritar la lantul majoritar validat

**Directie:**
Rezultatul e testabil simuland un fork manual (doua noduri mineaza simultan)
si verificand ca reteaua converge, in final, la un singur lant acceptat de
toate nodurile.

---

## Modulul 9 - Wallet si semnaturi digitale

**Domeniu:** criptografie asimetrica

**Cerinte tehnice minime:**
- Generare de pereche de chei (publica/privata) - se poate folosi o biblioteca
  existenta (ex. OpenSSL/libsodium)
- Semnarea unei tranzactii cu cheia privata a expeditorului
- Verificarea semnaturii (cu cheia publica) inainte ca o tranzactie sa fie
  acceptata intr-un bloc

**Directie:**
Rezultatul e un flux complet: o tranzactie nesemnata sau semnata gresit trebuie
respinsa de retea inainte de a ajunge intr-un bloc minat.

---

## Modulul 10 - API (Python)

**Domeniu:** dezvoltare web backend, integrare C-Python

**Cerinte tehnice minime:**
- Expunerea nucleului C ca biblioteca partajata (`.so`), apelabila din Python
  prin `ctypes` (sau alternativ, comunicare prin fisier/subprocess)
- Server REST minimal (Flask/FastAPI) cu cel putin trei endpoint-uri:
  vizualizare lant, trimitere tranzactie, declansare mining
- Raspunsuri in format JSON, coerente cu structura de date din nucleu

**Directie:**
Rezultatul e un API functional care poate fi testat direct (ex. cu `curl` sau
Postman), pregatit sa fie consumat ulterior de UI-ul din Modulul 11.
