template <base; random.Random(seed).randint(10000, 99999)>

template <flag1; "FLAG{" + str(base) + "">
template <flag2; "_" + str(base * 2 + 42) + "}">
template <flag1len; len(flag1)>
template <flag2len; len(flag2)>

template <keyrep; 4>
template <key; ''.join(random.choice(string.ascii_lowercase) for i in range(keyrep)) * (flag1len // keyrep + 1)>

template <flagt; ''.join(chr(ord(ch) ^ ord(k)) for ch, k in zip(flag1, key))>
template <flagtlen; len(flagt)>

chunk i : int
chunk key : [<keylen; len(key)>]char = <key>
chunk flag : [<flagtlen>]char = <flagt>

chunk fd : *FILE@libc.stdio = null

block main {
    ...

    puts@libc.stdio("I'm going to make a flag.")
    call makeflag

    ...

    sleep@libc.unistd(2)

    ...
    
    fd = fopen@libc.stdio("/dev/null", "w")
    fwrite@libc.stdio(flag, sizeof(char), <flagtlen>, fd)
    fclose@libc.stdio(fd)
    puts@libc.stdio("Wait, I've lost it!")

    ...
}

block makeflag {
    i = 0
    while i < <flagtlen> {
        flag[i] = flag[i] ^ key[i]
        i = i + 1
    }
}

