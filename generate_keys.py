import bcrypt
import warnings

# Suppress bcrypt warnings if any
warnings.filterwarnings("ignore", module="bcrypt")

passwords_to_hash = ['radio123', 'admin456',]
hashed_passwords = []

print("Hashing passwords...")

for password in passwords_to_hash:
    # 1. Encode the password to bytes
    password_bytes = password.encode('utf-8')
    
    # 2. Generate a "salt"
    salt = bcrypt.gensalt()
    
    # 3. Hash the password with the salt
    hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)
    
    # 4. Decode the hash back to a string to print it
    hashed_password_string = hashed_password_bytes.decode('utf-8')
    
    hashed_passwords.append(hashed_password_string)

print("\n--- SUCCESS! ---")
print("Copy the list below and paste it into your config.yaml file:\n")
print(f"passwords: {hashed_passwords}")