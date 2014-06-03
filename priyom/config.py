import os.path

base_path = os.path.abspath(os.getcwd())
data_base_path = None

templates_path = None
l10n_path = None
css_path = None
img_path = None

def recalc_paths():
    global base_path, data_base_path, templates_path, css_path, l10n_path, img_path

    if not data_base_path:
        data_base_path = os.path.join(base_path, "resources")

    templates_path = os.path.join(data_base_path, "templates")
    css_path = os.path.join(data_base_path, "css")
    l10n_path = os.path.join(data_base_path, "messages")
    img_path = os.path.join(data_base_path, "img")

recalc_paths()
