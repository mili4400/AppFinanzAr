import bcrypt
import json
import os
from typing import Dict, Any, Optional


class AuthManager:
    def __init__(self, users_file: str = "data/users_example.json"):
        self.users_file = users_file
        self.users = self._load_users()

    # ----------------------------
    # DEBUG LOGIN
    # ----------------------------
    def login(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        print("\n=============================")
        print("🔍 DEBUG LOGIN ACTIVADO")
        print("=============================")

        print(f"Usuario recibido: '{username}' (len={len(username)})")
        print(f"Password recibido: [NO SE MUESTRA] len={len(password)}")

        if username not in self.users:
            print("❌ Usuario no encontrado en el archivo JSON")
            print("Usuarios disponibles:", list(self.users.keys()))
            return None

        user_data = self.users[username]
        stored_hash = user_data["password_hash"]

        print(f"Hash guardado: '{stored_hash}' (len={len(stored_hash)})")

        try:
            password_bytes = password.encode("utf-8")
            hash_bytes = stored_hash.encode("utf-8")

            print("⚙ Ejecutando bcrypt.checkpw()...")
            result = bcrypt.checkpw(password_bytes, hash_bytes)

            print(f"Resultado checkpw = {result}")

            if result:
                print("✅ LOGIN EXITOSO")
                return user_data
            else:
                print("❌ CONTRASEÑA INCORRECTA")
                return None

        except Exception as e:
            print("💥 ERROR EN LOGIN:", e)
            return None

    # ----------------------------
    # Carga usuarios
    # ----------------------------
    def _load_users(self) -> Dict[str, Any]:
        print(f"[DEBUG] Cargando usuarios desde: {self.users_file}")

        if not os.path.exists(self.users_file):
            print("💥 Archivo de usuarios no encontrado.")
            return {}

        try:
            with open(self.users_file, "r") as f:
                users = json.load(f)
        except Exception as e:
            print("💥 Error leyendo JSON:", e)
            return {}

        print("[DEBUG] Usuarios cargados:")
        for u in users:
            print("   -", u["username"])

        return {u["username"]: u for u in users}

