from passlib.hash import sha256_crypt

salt = "password3"

pass1 = "password1" + salt
pass2 = "password2" + salt

salt1 = sha256_crypt.encrypt(pass1)
salt2 = sha256_crypt.encrypt(pass2)

print(salt1)
print(salt2)

print(sha256_crypt.verify("password1"+salt, salt1))

"""

## simple MD5 with salt
import hashlib

user_password = "cookies"
salt = "balooga"
new_password = user_password + salt
hashpass = hashlib.md5(new_password.encode())
print(hashpass.hexdigest())
"""