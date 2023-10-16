import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

def key_generator(username):
    user_dir = f"./{username}"
    if os.path.exists(user_dir):
        print("This user has already got a key pair!")
        return
    else:
        try:
            os.mkdir(user_dir)
            # os.chdir(user_dir)

            # generating private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            with open(f'./{username}/private_key.pem', 'wb') as f:
                f.write(pem)

            # generating public key
            public_key = private_key.public_key()

            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            with open(f'./{username}/public_key.pem', 'wb') as f:
                f.write(pem)

            print("Key pair generated successfully!")

        except Exception as e:
            print("Error: ", e)

# if __name__ == "__main__":
#     username = input("Enter your username: ")
#     key_generator(username)





