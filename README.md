# TexSkabelon

LaTeX-skabelon til rapporter på Aarhus Universitet (Institut for Elektro- og Computerteknologi) med AU-header, forside, forkortelser, kildeliste, bilag og automatisk tegntælling.

Skabelonen er sat op efter mine egne præferencer (skrifttype, layout, tabelstil, kildehenvisninger som fodnoter osv.), så tilpas gerne `Preamble.tex` og resten til dine egne.

Brug den med **Use this template** øverst på GitHub-siden.

📄 **[Se hvordan skabelonen ser ud (Eksempel.pdf)](Eksempel.pdf)**

## Krav

- **TeX Live / MacTeX** med `latexmk`, LuaLaTeX og `biber`.
- **Python 3** til tegntællingen (`tegntaelling.py`).
- **AU Passata** (valgfri): AU's egen skrifttype, som er gratis for studerende og medarbejdere. Hent den på [AU's side om skrifttyper](https://medarbejdere.au.dk/en/administration/communication/guidelines/guidelinesforfonts) og installér den i systemet (på macOS i `~/Library/Fonts`). Er den ikke installeret, bruges LaTeX' standardskrift.

## Byg

```bash
latexmk main.tex
```

`.latexmkrc` sørger for at bruge LuaLaTeX og biber, kører tegntællingen før hvert build og (kun i selve TexSkabelon-repoet, ikke i kopier) opdaterer `Eksempel.pdf` efter hvert vellykket build.

Med VS Code og udvidelsen **LaTeX Workshop** bygges rapporten automatisk, når du gemmer (se `.vscode/settings.json`).

> **Apple Silicon:** Hvis biber fejler med `extracting arm64 binary with lipo failed`, så lav en arm64-udgave. `.latexmkrc` bruger den automatisk, hvis den findes:
>
> ```bash
> mkdir -p ~/.local/bin && lipo $(which biber) -thin arm64 -output ~/.local/bin/biber-arm64
> ```

## Struktur

| Fil / mappe | Indhold |
| --- | --- |
| `main.tex` | Rapportens rækkefølge: forside, indhold, forkortelser, kapitler, kildeliste, bilag |
| `Preamble.tex` | Pakker, skrifttype, sidelayout, header og footer |
| `Kapitler/` | Et kapitel pr. fil. `Forside.tex` udfyldes med titel, dato, navn og studienummer |
| `Kapitler/Eksempler.tex` | Eksempler på figurer, tabeller, formler, kode, kilder og henvisninger. Slet det, når du ikke skal bruge det |
| `Bilag/` | Bilag (bliver til "Bilag A", "Bilag B", …) og PDF-filer, der indsættes med `\includepdf` |
| `Billeder/` | Billeder. Skrives uden sti: `\includegraphics{navn.png}` |
| `Forkortelser.tex` | Forkortelser, brugt med `\ac{nøgle}` |
| `references.bib` | Kilder, brugt med `\cite{nøgle}` (kan eksporteres fra Zotero) |
| `tegntaelling.py` | Tæller tegn i brødteksten (1 normalside = 2400 tegn) og viser det på forsiden |

Hvert kapitel er en `subfiles`-fil, så det også kan kompileres for sig selv.

## Nyt kapitel

1. Kopiér `Kapitler/Indledning.tex` til fx `Kapitler/Analyse.tex`.
2. Tilføj `\subfile{Kapitler/Analyse}` i `main.tex` mellem `\pagenumbering{arabic}` og `\printbibliography`.

Kun kapitler i det område tælles med i tegntællingen. Forside, indholdsfortegnelse, kildeliste og bilag tælles ikke med, og det gør kommentarer, `\todo`, fodnoter, figurer, tabeller, kode og formler heller ikke.

## Nyttige kommandoer

| Kommando | Resultat |
| --- | --- |
| `\todo{...}`, `\todo[inline]{...}` | Note i margenen eller i teksten. Alle noter listes forrest i rapporten |
| `\cref{fig:x}` | "figur 1", "tabel 2", "afsnit 3", "bilag A" … |
| `\ac{au}` | Forkortelse: første gang "Aarhus Universitet (AU)", derefter "AU" |
| `\cite{nøgle}` | Kildehenvisning som fodnote |
| `\qty{6,5}{\kilo\watt}`, `\num{1234,5}` | Tal og enheder i dansk format |
| `\lipsum[1-2]` | Fyldtekst (tælles ikke med) |
