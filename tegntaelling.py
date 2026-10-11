#!/usr/bin/env python3
"""Tæller tegn inkl. mellemrum i rapportens brødtekst (1 normalside = 2400 tegn).

Tæller kapitlerne, der indlæses med \\subfile i main.tex efter \\pagenumbering{arabic}
og før \\printbibliography / \\begin{appendices}. Forside, indholdsfortegnelse,
forkortelser, kildeliste og bilag tælles altså ikke med.

I kapitlerne tælles IKKE: kommentarer, \\todo, \\cite/kildehenvisninger, fodnoter,
\\label, figurer, tabeller, kodeblokke, formler og \\lipsum-fyldtekst.
Forkortelser (\\ac{...}) udfoldes som i PDF'en: første gang "lang form (KORT)".

Kør: python3 tegntaelling.py  (køres også automatisk ved hvert build via .latexmkrc)
Skriver Antal-tegn.tex med \\antaltegn og \\antalnormalsider, som kan bruges i rapporten.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEGN_PR_NORMALSIDE = 2400

# Environments whose whole content is skipped
SKIP_ENVS = ["figure", "figure*", "table", "table*", "tabular", "tabularx", "longtable",
             "lstlisting", "equation", "equation*", "align", "align*", "comment", "tikzpicture"]
# Commands removed together with all their arguments
DROP_CMDS = ["todo", "cite", "autocite", "footcite", "parencite", "textcite", "footnote",
             "label", "includegraphics", "includepdf", "lipsum", "vspace", "hspace",
             "newpage", "clearpage", "noindent", "printacronyms", "printbibliography",
             "addcontentsline", "phantomsection", "centering", "caption"]
# Commands replaced with a short stand-in for what they print
REF_CMDS = {"ref": "1", "cref": "afsnit 1", "Cref": "Afsnit 1", "pageref": "1", "eqref": "(1)"}
HEADING_CMDS = ["section", "subsection", "subsubsection", "paragraph"]


def strip_comments(tex):
    return re.sub(r"(?<!\\)%.*", "", tex)


def read_group(tex, i, open_c="{", close_c="}"):
    """Return (content, end_index) of the balanced group starting at tex[i] == open_c."""
    depth, j = 0, i
    while j < len(tex):
        c = tex[j]
        if c == "\\":
            j += 2
            continue
        if c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                return tex[i + 1:j], j + 1
        j += 1
    return tex[i + 1:], len(tex)


def skip_args(tex, i, mandatory_only=False):
    """Skip optional [..] and mandatory {..} arguments after a command; return (args, index)."""
    args = []
    while True:
        k = i
        while k < len(tex) and tex[k] in " \t":
            k += 1
        if k < len(tex) and tex[k] in "[{":
            content, i = read_group(tex, k, tex[k], "]" if tex[k] == "[" else "}")
            if tex[k] == "{" or not mandatory_only:
                args.append(content)
        else:
            return args, i


def load_acronyms():
    acros = {}
    path = ROOT / "Forkortelser.tex"
    if path.exists():
        tex = strip_comments(path.read_text(encoding="utf-8"))
        for m in re.finditer(r"\\DeclareAcronym\{([^}]*)\}\s*\{", tex):
            body, _ = read_group(tex, m.end() - 1)
            fields = dict(re.findall(r"(\w[\w-]*)\s*=\s*([^,\n]+)", body))
            acros[m.group(1).strip()] = {k: v.strip().replace("\\&", "&") for k, v in fields.items()}
    return acros


class Counter:
    def __init__(self):
        self.acros = load_acronyms()
        self.used = set()
        self.lipsums = 0

    def acro(self, cmd, key):
        a = self.acros.get(key, {"short": key, "long": key})
        short, long_ = a.get("short", key), a.get("long", key)
        plural = cmd.endswith("p")
        s = short + ("s" if plural else "")
        l = long_
        if cmd in ("acs", "acsp"):
            return s
        if cmd in ("acl", "aclp"):
            return l
        if cmd in ("acf", "acfp") or key not in self.used:
            self.used.add(key)
            return f"{l} ({s})"
        return s

    def to_text(self, tex):
        """Convert LaTeX source to the plain text it prints (approximately)."""
        out, i = [], 0
        while i < len(tex):
            c = tex[i]
            if c == "\\":
                m = re.match(r"\\([A-Za-z]+\*?|.)", tex[i:])
                name = m.group(1)
                i += m.end()
                if name in ("begin", "end"):
                    env, i = read_group(tex, i)
                    if name == "begin" and env in SKIP_ENVS:
                        end = tex.find("\\end{" + env + "}", i)
                        i = len(tex) if end < 0 else end + len("\\end{" + env + "}")
                    out.append(" ")
                    continue
                base = name.rstrip("*")
                if base in DROP_CMDS:
                    if base == "lipsum":
                        self.lipsums += 1
                    _, i = skip_args(tex, i)
                    continue
                if base in REF_CMDS:
                    _, i = skip_args(tex, i)
                    out.append(REF_CMDS[base])
                    continue
                if re.fullmatch(r"ac[slf]?p?", base):
                    args, i = skip_args(tex, i, mandatory_only=True)
                    out.append(self.acro(base, args[-1].strip()) if args else "")
                    continue
                if base in HEADING_CMDS:
                    args, i = skip_args(tex, i, mandatory_only=True)
                    out.append("\n\x00H" + self.to_text(args[-1] if args else "") + "\x00\n")
                    continue
                if name == "\\":
                    _, i = skip_args(tex, i)
                    out.append(" ")
                elif name in "&%$#_{}":
                    out.append(name)
                elif name == " " or name == ",":
                    out.append(" ")
                elif name == "item":
                    args, i = skip_args(tex, i)
                    out.append(" " + " ".join(self.to_text(a) for a in args) + " ")
                else:
                    # Unknown/formatting command (\textbf, \emph, ...): keep the text of its {} args
                    args, i = skip_args(tex, i, mandatory_only=True)
                    out.append("".join(self.to_text(a) for a in args))
                continue
            if c == "$":
                end = tex.find("$", i + 1)
                i = len(tex) if end < 0 else end + 1
                out.append("x")  # inline math counts as one symbol
                continue
            if c in "{}":
                i += 1
                continue
            if c == "~":
                out.append(" ")
                i += 1
                continue
            out.append(c)
            i += 1
        text = "".join(out)
        return text.replace("---", "—").replace("--", "–").replace("``", "“").replace("''", "”")


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def chapter_files():
    main = strip_comments((ROOT / "main.tex").read_text(encoding="utf-8"))
    start = main.find("\\pagenumbering{arabic}")
    ends = [p for p in (main.find("\\printbibliography"), main.find("\\begin{appendices}")) if p >= 0]
    body = main[start if start >= 0 else 0:min(ends) if ends else len(main)]
    return [ROOT / (f if f.endswith(".tex") else f + ".tex")
            for f in re.findall(r"\\subfile\{([^}]*)\}", body)]


def main():
    counter = Counter()
    rows, total_text, total_head = [], 0, 0
    for path in chapter_files():
        tex = strip_comments(path.read_text(encoding="utf-8"))
        m = re.search(r"\\begin\{document\}(.*)\\end\{document\}", tex, re.S)
        raw = counter.to_text(m.group(1) if m else tex)
        headings = re.findall(r"\x00H(.*?)\x00", raw, re.S)
        body = re.sub(r"\x00H.*?\x00", " ", raw, flags=re.S)
        n_text = len(normalize(body))
        n_head = sum(len(normalize(h)) for h in headings)
        rows.append((path.relative_to(ROOT), n_text, n_head))
        total_text += n_text
        total_head += n_head

    total = total_text + total_head
    print("Tegn inkl. mellemrum (1 normalside = 2400 tegn)")
    for name, t, h in rows:
        print(f"  {str(name):38} {t:7d} tekst  {h:5d} overskrifter")
    print(f"  {'I alt':38} {total_text:7d} tekst  {total_head:5d} overskrifter")
    print(f"  Samlet: {total} tegn = {total / TEGN_PR_NORMALSIDE:.2f} normalsider")
    if counter.lipsums:
        print(f"  NB: {counter.lipsums} \\lipsum-fyldtekst er ikke talt med.")

    tegn = f"{total:,}".replace(",", ".")                         # 12.345
    sider = f"{total / TEGN_PR_NORMALSIDE:.1f}".replace(".", ",")   # 5,1
    (ROOT / "Antal-tegn.tex").write_text(
        "% Genereret af tegntaelling.py - rediger ikke i hånden\n"
        f"\\newcommand{{\\antaltegn}}{{{tegn}}}\n"
        f"\\newcommand{{\\antalnormalsider}}{{{sider}}}\n",
        encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
