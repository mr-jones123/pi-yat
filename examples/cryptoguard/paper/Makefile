all: main.pdf

main.pdf: main.tex references.bib
	pdflatex -interaction=nonstopmode main
	bibtex main
	pdflatex -interaction=nonstopmode main
	pdflatex -interaction=nonstopmode main

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.pdf *.toc *.fdb_latexmk *.fls *.synctex.gz

.PHONY: all clean
