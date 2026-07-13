# Blockchain: Tehnologia care schimba increderea digitala

## Slide 1 — Titlu
**Blockchain: Tehnologia care schimba increderea digitala**

- Subtitlu: Ce este, cum functioneaza si de ce conteaza
- Nume, grupa, disciplina
- Data prezentarii

---

## Slide 2 — Ce este blockchain-ul?
**Idee centrala:** Un registru digital distribuit, imutabil si descentralizat

- Definitie simpla: o baza de date partajata intre mai multi participanti, fara o autoritate centrala
- Cele 3 caracteristici cheie: **descentralizare, imutabilitate, transparenta**
- Analogie: un "caiet de contabilitate" copiat identic la mii de persoane, unde toti vad aceleasi inregistrari
- De ce e diferit de o baza de date clasica (SQL/NoSQL) — nu exista un singur "stapan" al datelor

---

## Slide 3 — Structura de baza: blocuri si hash-uri
**Idee centrala:** Lantul este format din blocuri legate criptografic

- Ce contine un bloc: date (tranzactii), timestamp, hash propriu, hash-ul blocului anterior
- Functia hash (ex. SHA-256): transforma orice input intr-un sir fix de lungime, ireversibil
- De ce legatura prin hash face lantul imutabil — modificarea unui bloc rupe toate hash-urile urmatoare
- Legatura cu proiectul propriu: implementarea SHA-256 si structura de bloc in C

---

## Slide 4 — Cum functioneaza: de la tranzactie la bloc validat
**Idee centrala:** Fluxul unei tranzactii, pas cu pas

- Pasul 1: utilizatorul initiaza o tranzactie (semnata digital)
- Pasul 2: tranzactia e transmisa in retea (broadcast catre noduri)
- Pasul 3: nodurile valideaza tranzactia (verificare semnatura, fonduri disponibile)
- Pasul 4: tranzactiile validate sunt grupate intr-un bloc candidat
- Pasul 5: blocul e "minat"/validat si adaugat oficial in lant

---

## Slide 5 — Consensul distribuit: cum se pun de acord nodurile
**Idee centrala:** Mecanisme de consens — Proof of Work vs Proof of Stake

- Problema de baza: cum ai incredere intr-o retea fara autoritate centrala?
- **Proof of Work (PoW):** rezolvarea unei probleme computationale costisitoare (mining) — folosit de Bitcoin
- **Proof of Stake (PoS):** validatorii "pun la bataie" monede ca garantie — folosit de Ethereum (dupa 2022)
- Comparatie: consum energetic, viteza, securitate, centralizare a puterii

---

## Slide 6 — Descentralizare vs sisteme centralizate
**Idee centrala:** De ce elimini intermediarul central

- Model centralizat clasic: banca, notar, platforma — un singur punct de control (si esec)
- Model descentralizat: mii de noduri identice, fara punct unic de vulnerabilitate
- Rezistenta la cenzura si la manipulare — un nod compromis nu afecteaza reteaua
- Compromis: descentralizarea completa costa in viteza si scalabilitate

---

## Slide 7 — Criptomonedele — prima aplicatie majora
**Idee centrala:** Bitcoin si Ethereum ca prime cazuri de utilizare reale

- Bitcoin (2009): bani digitali fara banca centrala, oferta limitata (21 milioane)
- Ethereum (2015): blockchain programabil, nu doar transfer de valoare
- Ce problema reala rezolva: transfer de valoare peer-to-peer, fara intermediar, transfrontalier
- Volatilitate si perceptia publica vs. utilitate tehnica reala

---

## Slide 8 — Smart contracts: blockchain dincolo de bani
**Idee centrala:** Cod care se executa automat, fara intermediar uman

- Ce este un smart contract: program stocat pe blockchain, executat automat la indeplinirea unor conditii
- Exemplu simplu: „daca X plateste Y, atunci se elibereaza automat produsul/serviciul"
- Aplicatii: DeFi (finante descentralizate), DAO-uri (organizatii autonome descentralizate)
- Riscuri: bug-uri in cod = pierderi ireversibile (exemplu: hack-uri celebre din DeFi)

---

## Slide 9 — Utilizare in viata de zi cu zi
**Idee centrala:** Blockchain dincolo de criptomonede

- **Supply chain / logistica:** trasabilitatea produselor (alimente, medicamente, produse de lux)
- **Sanatate:** stocarea securizata si partajarea controlata a dosarelor medicale
- **Vot electronic:** transparenta si imposibilitatea alterarii rezultatelor
- **Identitate digitala:** control propriu asupra datelor personale, fara dependenta de o singura platforma
- **NFT-uri:** proprietate digitala verificabila (arta, licente, certificate)

---

## Slide 10 — Avantaje si limitari
**Idee centrala:** Un bilant realist al tehnologiei

- **Avantaje:** transparenta, securitate criptografica, rezistenta la cenzura, eliminarea intermediarilor
- **Limitari:** scalabilitate redusa (tranzactii/secunda mici comparativ cu Visa), consum energetic (mai ales PoW)
- Problema „trilemei blockchain": descentralizare vs securitate vs scalabilitate — greu de optimizat toate 3 simultan
- Costuri de tranzactie variabile (gas fees)

---

## Slide 11 — Utilitatea actuala (2025-2026)
**Idee centrala:** Unde se afla tehnologia acum, in practica

- Adoptie institutionala: banci si companii mari care testeaza blockchain intern
- Reglementari in curs de definitivare (UE, SUA) — cadru legal tot mai clar
- Tendinte: tokenizarea activelor reale (imobiliare, actiuni), stablecoins
- Integrare cu AI: verificare de provenienta a datelor, contracte inteligente automate prin agenti AI

---

## Slide 12 — Concluzii
**Idee centrala:** De ce conteaza si incotro se indreapta

- Blockchain = infrastructura de incredere descentralizata, nu doar „bani digitali"
- Aplicabilitate larga: finante, sanatate, guvernare, proprietate digitala
- Provocari ramase: scalabilitate, reglementare, adoptie masiva
- Directie viitoare: integrare tot mai profunda in servicii digitale cotidiene