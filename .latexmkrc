# TeX Live's universal biber fails on Apple Silicon ("extracting arm64 binary with lipo failed").
# Use an arm64-only copy if it exists, extracted with: lipo $(which biber) -thin arm64 -output ~/.local/bin/biber-arm64
if (-e "$ENV{HOME}/.local/bin/biber-arm64") {
    $biber = "$ENV{HOME}/.local/bin/biber-arm64 %O %S";
}

# Always build a PDF with LuaLaTeX, needed for system fonts like AU Passata
# (LaTeX Workshop's latexmk tool doesn't pass an engine flag)
$pdf_mode = 4;
# Even if latexmk is called with -pdf (pdflatex mode), run LuaLaTeX instead
$pdflatex = "lualatex %O %S";

# Count characters in the body text before every build; writes Antal-tegn.tex (shown on the cover)
system("python3", "tegntaelling.py");

# After a successful build of main.tex, copy main.pdf to Eksempel.pdf (the example PDF linked from README.md).
# Only in the TexSkabelon repo itself, not in reports created from the template.
END {
    my $status = $?;  # latexmk's exit status; the backticks below overwrite $?
    my $remote = `git config --get remote.origin.url 2>/dev/null`;
    if ($status == 0 && $remote =~ m{kasp734e/TexSkabelon} && -e "main.pdf" && -e "main.tex") {
        require File::Copy;
        File::Copy::copy("main.pdf", "Eksempel.pdf");
    }
    $? = $status;     # keep latexmk's exit status
}
