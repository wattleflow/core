---
name: wattleflow-core-index
description: Regenerira katalog `wattleflow.core` sučelja alatom `core/tools/core_index.py` — VS Code snippete (`wf` prefiks) i Markdown pregled — te mjeri usklađenost docstringova s konvencijom. Koristi kad korisnik traži ažuriranje snippeta, pregled sučelja, ili nakon izmjene u `core/` koja je dodala, uklonila ili preimenovala sučelje.
---

# Katalog core sučelja

Predmet je **generirani pogled** na `wattleflow.core`: 86 sučelja čije docstringove alat čita
i pretvara u dva izlaza — snippete za dosjećanje u editoru i Markdown za čitanje.

**Pogled nije izvor istine (D-13).** Izvor je docstring u kodu. Ništa se u izlazima ne ispravlja
ručno — ispravlja se docstring pa se regenerira.

## 1. Gdje što živi

| artefakt | putanja | praćeno |
|---|---|---|
| alat | `core/tools/core_index.py` | da |
| test alata | `core/tools/tests/test_core_index.py` | da |
| snippeti | `<repo>/.vscode/wattleflow-core.code-snippets` ×3 | **ne** — `.vscode` je gitignoriran u sva tri repozitorija |
| pregled | `documentation/core/INTERFACES.md` | da (doc repozitorij) |
| dijagrami | `documentation/core/uml/*.puml` + `*.jpg` | da (doc repozitorij) |

Snippeti su **izlaz, ne izvor**: nestaju na svježem klonu i vraća ih regeneracija. Zato se pišu
na sve tri lokacije — VS Code čita `.code-snippets` samo iz `.vscode/` **otvorene** mape, a
`*.code-workspace` ne postoji.

## 2. Regeneracija — jedna naredba

```bash
cd ~/projects/wattleflow/core
python tools/core_index.py \
  --snippets ~/projects/wattleflow/core/.vscode/wattleflow-core.code-snippets \
  --snippets ~/projects/wattleflow/processors/.vscode/wattleflow-core.code-snippets \
  --snippets ~/projects/wattleflow/workflow/.vscode/wattleflow-core.code-snippets \
  --uml documentation/uml \
  --markdown documentation/INTERFACES.md
```

`--uml` piše jedan PlantUML class dijagram po sučelju; uz `--markdown` pregled ugrađuje
rasteriziranu sliku svakog. **Rasterizacija je drugi korak i nije u alatu** (core alati su
stdlib-only, PlantUML traži Javu) — recept i gledište dijagrama drži
[`documentation/core/uml/README.md`](../../../../documentation/core/uml/README.md). Nakon
izmjene `.puml`-a **rasterizaciju treba pokrenuti**, inače `INTERFACES.md` pokazuje stare slike.

Alat briše `.puml` bez sučelja, ali ne dira `.jpg` — datoteke koje ne stvara ne uklanja.

`documentation/` u core repozitoriju je symlink na `documentation/core/` u doc repozitoriju —
pisanje kroz njega je namjerno, sadržaj se ne duplicira.

**Nakon regeneracije javi korisniku da VS Code mora ponovno učitati prozor**
(`Ctrl+Shift+P` → `Developer: Reload Window`); snippeti se čitaju pri otvaranju mape.

Izostavljanje oba prekidača ispisuje samo sažetak po modulu i ništa ne piše — koristi to kad
provjeravaš stanje, ne kad ažuriraš.

## 3. Mjerenje konvencije — obvezno uz svaku regeneraciju

```bash
python tools/core_index.py --check    # izlazni kod 1 ako išta odstupa
```

Alat prepoznaje tri odstupanja: **nema docstringa**, uvodna linija nije `Ime - uloga`, **nema
`Interface:` bloka**. Zatečeno stanje je `80/86` — šest sučelja bez docstringa.

Pravila izvještavanja:

- **Broj odstupanja uvijek javi korisniku**, i kad je nepromijenjen. Nemjereno se ne smije
  čitati kao čisto (§9).
- **Porast broja nije kvar alata nego drift izvora** — netko je dodao sučelje bez docstringa.
  To je nalaz o `core/`, prijavi ga kao takav.
- **Ne popravljaj docstringove usput.** `core/` se mijenja samo dokumentiranom izmjenom (§2.5);
  predloži izmjenu, ne izvedi je.
- U izlazima odstupanje je vidljivo kao `(role not declared)` — to je deklarirana rupa (D-11),
  ne greška renderiranja; ne skrivaj je.

## 4. Kad se mijenja sam alat

Test je uz alat, izvan `--src` opsega:

```bash
cd ~/projects/wattleflow/core
python -m unittest discover -s tools/tests -v
ruff check tools/core_index.py tools/tests/test_core_index.py
ruff format tools/core_index.py tools/tests/test_core_index.py
```

**Svaka nova tvrdnja o alatu traži test, a svaki test mutacijsku provjeru**: namjerno pokvari
alat na mjestu koje tvrdnja pokriva i dokaži da test padne. Tvrdnja koju nijedna mutacija ne
obori nije provjerena, nego napisana.

Zatečene mutacije koje suite hvata: `removeprefix`→`lstrip` (stem imena), prihvaćanje
neapstraktnih metoda u ugovor, prestanak preskakanja dunder modula, prazna uloga umjesto oznake,
`--check` koji uvijek javlja uspjeh. Za dijagrame: ukinut prag lepeze, potparametrizirana baza
u vlastitoj kutiji, zadržan `self` u parametrima, vezanje pročitano mimo dekoratora, ponovljeni
vanjski brid, preci bez članova, zaostali `.puml`, izgubljena relativna putanja slike, drift
`.jpg`/`.png`, istaknuta svaka kutija, progutan `Finding:`, ispušteni tipski parametri i
ispuštena bilješka naslijeđenog ugovora.

**Fixture se ne dimenzionira iz konstante koju testira.** Lepeza u testu je literal, ne
`MAX_CHILDREN + 1`: fixture koji raste s pragom ne bi primijetio da je prag ukinut.

Ograničenja koja se ne smiju ukloniti bez razloga:

- **Alat čita AST, nikad ne importa** `wattleflow.core` — mora raditi nad checkoutom koji nije
  instaliran.
- **Stdlib only.** Core `.gitignore` fiksira da su mu alati stdlib-only i da konfiguraciju drže
  isključivo u JSON-u (`*.yaml`/`*.yml` su ignorirani).
- **Potpisi dolaze iz AST-a, ne iz `Interface:` bloka.** Blok je opisni tekst koji može odlutati
  od koda; apstraktne metode ne mogu. Blok se koristi samo kao zamjena kad sučelje nema vlastitu
  apstraktnu metodu.
- Alat nije u paketu (`MANIFEST.in` počinje s `global-exclude *`), pa §7.1 na njega ne djeluje —
  ali stdlib ograničenje vrijedi svejedno.
- Novi alat **ne smije završiti** u `tools/` popisu u `.gitignore`.

## 5. Što alat ne radi

Ne provjerava slaže li se `Interface:` blok s apstraktnim metodama, ne pokriva `concrete/` ni
specijalizacije, i ne rasterizira dijagrame koje generira. Mjerenje konvencije je kandidat za pravilo u
`core/tools/wem_lint.py`; dok ondje ne uđe, `--check` se pokreće **na zahtjev**, kao i lint —
dakle „strojno provjerljivo" i dalje znači provjeru koju netko pokrene.

`documentation/core/` nije naveden u `CLAUDE.md` §3.1. Dodavanje u stablo traži dokumentiranu izmjenu (D-03);
do tada je to deklarirana rupa, ne prešutna praksa.
