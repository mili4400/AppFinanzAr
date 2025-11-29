
import json, bcrypt, os

DATA_PATH="data/users_example.json"

class AuthManager:
    def __init__(self):
        self.users=self._load()

    def _load(self):
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH,"r") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(DATA_PATH,"w") as f:
            json.dump(self.users,f,indent=2)

    def login(self, user, pwd):
        for u in self.users:
            if u["username"]==user:
                if bcrypt.checkpw(pwd.encode(), u["password_hash"].encode()):
                    return True
        return False

    def create_user(self, user, pwd, role="user", email=""):
        hashed=bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        self.users.append({
            "username":user,
            "password_hash":hashed,
            "role":role,
            "email":email
        })
        self._save()
