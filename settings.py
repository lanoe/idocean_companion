import json

class Singleton(object):
    _instances = {}
    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            class_._instances[class_] = super(Singleton, class_).__new__(class_, *args, **kwargs)
        return class_._instances[class_]

class Config(Singleton):
    def __init__(self, fichier_config="config.json"):
        self.fichier = fichier_config
        self.data = self._charger_config()

    def _charger_config(self):
        try:
            with open(self.fichier, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def sauvegarder(self):
        with open(self.fichier, 'w') as f:
            json.dump(self.data, f, indent=2)

    def get_all(self):
        return self.data

def parse_form_to_dict(form_data):
    result = {}
    for key, value in form_data.items():
        keys = key.split('[')
        current = result
        for i, k in enumerate(keys):
            k = k.rstrip(']')
            if i == len(keys) - 1:
                # Conversion des types
                if value == 'on':
                    current[k] = True
                elif value == '':
                    current[k] = False
                else:
                    try:
                        current[k] = int(value)
                    except ValueError:
                        try:
                            current[k] = float(value)
                        except ValueError:
                            current[k] = value
            else:
                if k not in current:
                    current[k] = {}
                current = current[k]
    return result