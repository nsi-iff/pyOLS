all: languages.ps

%.ps: %.dot
	dot -Tps2 $^ > $@
