TEAGETTEXT=PYTHONPATH=../teapot ../teapot/utils/teagettext.py

LOCALE_PATH=resources/messages
LOCALE_SRC_PATH=resources/messages_src
LOCALES=en_gb de_de
LOCALE_FILES=$(addsuffix .mo,$(addprefix $(LOCALE_PATH)/,$(LOCALES)))

GENERATED_FILES=priyom/model/format_parser_gen.py

run: $(LOCALE_FILES) $(GENERATED_FILES)
	./serve.py

priyom/model/format_parser_gen.py: support-files/format-definition.grammar support-files/pyLR1/pyLRp/parsers/pyLRparser.py
	cd support-files/pyLR1; python3 -m pyLRp -lLd3 -o ../../$@ ../../$<

support-files/pyLR1/pyLRp/parsers/pyLRparser.py:
	cd support-files/pyLR1; python3 -m pyLRp -lLd3 --bootstrap pyLRp/parsers/pyLRparser.pyLRp

$(LOCALE_PATH):
	mkdir -p $@

$(LOCALE_PATH)/%.mo: $(LOCALE_SRC_PATH)/%.po $(LOCALE_PATH)
	msgfmt --output-file=$@ $<

rescan:
	$(TEAGETTEXT) -oresources/messages_src/from_xml.pot -D resources/templates
	cd resources/messages_src; cat from_xml.pot static.pot > all.pot
	find resources/messages_src -iname "*.po" -print0 | xargs -0 -n1 -I{} -- msgmerge -U {} resources/messages_src/all.pot

.PHONY: run rescan
