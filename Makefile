LOCALE_PATH=resources/messages
LOCALE_SRC_PATH=resources/messages_src
LOCALES=en_gb de_de
LOCALE_FILES=$(addsuffix .mo,$(addprefix $(LOCALE_PATH)/,$(LOCALES)))

run: $(LOCALE_FILES)
	./serve.py

$(LOCALE_PATH): 
	mkdir -p $@

$(LOCALE_PATH)/%.mo: $(LOCALE_SRC_PATH)/%.po $(LOCALE_PATH)
	msgfmt --output-file=$@ $<
