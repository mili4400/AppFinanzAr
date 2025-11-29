
import json

def load_json(path, default=None):
    try:
        with open(path,"r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, obj):
    with open(path,"w") as f:
        json.dump(obj,f,indent=2)
