# generar_hash.py - script suelto para sacar el hash de una contraseña
import bcrypt  # la misma librería que uso en seguridad.py

password = input("Contraseña: ")  # pido la contraseña por consola
hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())  # genero el hash con salt
print(hash.decode())  # lo imprimo para copiarlo en el INSERT