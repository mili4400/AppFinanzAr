import json, bcrypt, os

# Ruta absoluta segura
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "users_example.json")
DATA_PATH = os.path.normpath(DATA_PATH)

class AuthManager:
    def __init__(self):
        print("🔍 [DEBUG] AuthManager inicializado")
        print(f"🔍 [DEBUG] Cargando usuarios desde: {DATA_PATH}")
        self.users = self._load()

        # Mostrar usuarios encontrados
        print(f"🔍 [DEBUG] Usuarios cargados ({len(self.users)}):")
        for u in self.users:
            print("     -", u.get("username"), "| hash:", u.get("password_hash"))

    def _load(self):
        if os.path.exists(DATA_PATH):
            try:
                with open(DATA_PATH, "r") as f:
                    data = json.load(f)
                    print("🔍 [DEBUG] Archivo JSON leído correctamente.")
                    return data
            except Exception as e:
                print("❌ [ERROR] No se pudo leer el archivo JSON:", e)
                return []
        else:
            print("❌ [ERROR] No existe el archivo en ruta:", DATA_PATH)
        return []

    def _save(self):
        try:
            with open(DATA_PATH, "w") as f:
                json.dump(self.users, f, indent=2)
            print("💾 [DEBUG] Archivo JSON actualizado correctamente.")
        except Exception as e:
            print("❌ [ERROR] No se pudo guardar el archivo JSON:", e)

    def login(self, user, pwd):
        print(f"🔐 [DEBUG] Intento de login → usuario ingresado: {user}")

        for u in self.users:
            print(f"    ⤷ Comparando con usuario: {u['username']}")
            if u["username"] == user:
                print("    ✔ Usuario encontrado. Verificando password…")
                ok = bcrypt.checkpw(pwd.encode(), u["password_hash"].encode())
                print("    ✔ Resultado bcrypt:", ok)
                return ok

        print("    ❌ Usuario NO encontrado.")
        return False

    def create_user(self, user, pwd, role="user", email=""):
        print(f"🆕 [DEBUG] Creando usuario: {user}")
        hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

        self.users.append({
            "username": user,
            "password_hash": hashed,
            "role": role,
            "email": email
        })

        self._save()
        print("🆕 ✔ Usuario creado correctamente.")


       
