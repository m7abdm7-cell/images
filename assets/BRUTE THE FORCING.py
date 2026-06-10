import hashlib
import bcrypt

if __name__ == "__main__":
    print("GJP2 Value Generator For GDPS Database (Press Ctrl+C to exit)")
    print("=" * 60)

    try:
        while True:
            password = input("\nEnter the plain-text password to hash: ").strip()
            
            if not password:
                print("Password cannot be empty. Please try again.")
                continue

            password_bytes = password.encode("utf-8")
            salt_password = bcrypt.gensalt(rounds=12, prefix=b"2b")
            salt_password_2y = salt_password.decode("utf-8").replace("$2b$", "$2y$").encode("utf-8")
            db_password_hash = bcrypt.hashpw(password_bytes[:72], salt_password_2y).decode("utf-8")
            print(password_bytes)

            gjp2_salt = "mI29fmAnxgTs"
            client_gjp2_string = hashlib.sha1((password + gjp2_salt).encode("utf-8")).hexdigest()

            gjp2_bytes = client_gjp2_string.encode("utf-8")
            salt_gjp2 = bcrypt.gensalt(rounds=12, prefix=b"2b")
            salt_gjp2_2y = salt_gjp2.decode("utf-8").replace("$2b$", "$2y$").encode("utf-8")
            db_gjp2_hash = bcrypt.hashpw(gjp2_bytes, salt_gjp2_2y).decode("utf-8")

            print("\n" + "-" * 40)
            print(f"password: {db_password_hash}")
            print(f"gjp2:     {db_gjp2_hash}")
            print("-" * 40)

    except KeyboardInterrupt:
        print("\nExiting generator...")