
from core.auth import AuthManager

auth=AuthManager()
u=input("Nuevo usuario: ")
p=input("Contraseña: ")

auth.create_user(u,p,role="user",email="")
print("Usuario creado.")
