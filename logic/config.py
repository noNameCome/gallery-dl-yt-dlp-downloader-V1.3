import os
import json

CONFIG_STORE = os.path.join(os.path.expanduser("~"), ".gallery_dl_gui_config.json")

def load_stored_output_dir():
    if os.path.exists(CONFIG_STORE):
        try:
            with open(CONFIG_STORE, 'r', encoding='utf-8') as f:
                return json.load(f).get("last_output_dir")
        except:
            return None

def store_output_dir(path):
    try:
        with open(CONFIG_STORE, 'w', encoding='utf-8') as f:
            json.dump({"last_output_dir": path}, f, indent=4)
    except:
        pass
