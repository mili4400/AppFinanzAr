import json
import bcrypt
import os

# Construir ruta absoluta hacia data/users_example.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "users_example.json")
DATA_PATH = os.path.normpath(DATA_PATH)


class AuthManager:
    def __init__(self):
        self.users = self._load()

    def _load(self):
        # Debug opcional para ver qué archivo se está cargando
        print(f"[Auth] Cargando usuarios desde: {DATA_PATH}")

        if os.path.exists(DATA_PATH):
            try:
                with open(DATA_PATH, "r") as f:
                    data = json.load(f)
                    print(f"[Auth] Usuarios cargados: {[u['username'] for u in data]}")
                    return data
            except Exception as e:
                print("[Auth] Error leyendo archivo de usuarios:", e)
                return []
        else:
            print("[Auth] Archivo de usuarios NO encontrado:", DATA_PATH)
        return []

    def _save(self):
        try:
            with open(DATA_PATH, "w") as f:
                json.dump(self.users, f, indent=2)
            print("[Auth] Usuarios guardados exitosamente.")
        except Exception as e:
            print("[Auth] Error guardando usuarios:", e)

    def login(self, user, pwd):
        for u in self.users:
            if u.get("username") == user:
                try:
                    if bcrypt.checkpw(pwd.encode(), u["password_hash"].encode()):
                        print(f"[Auth] Login correcto para usuario '{user}'")
                        return True
                except Exception as e:
                    print("[Auth] Error verificando contraseña:", e)
        print(f"[Auth] Login fallido para usuario '{user}'")
        return False

    def create_user(self, user, pwd, role="user", email=""):
        hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        new_user = {
            "username": user,
            "password_hash": hashed,
            "role": role,
            "email": email
        }

        self.users.append(new_user)
        self._save()
        print(f"[Auth] Usuario creado: {user}")

