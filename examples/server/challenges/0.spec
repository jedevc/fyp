// [compile]
// arch = 32
// debug = true
// debug_separate = true
//
// [env]
// type = tcp-shell-setuid
// port = 4000

chunk buffer: [<B; 8 * random.randint(4, 16)>]char = "",
      modified: int = <X; random.randint(0, 100)>

block main {
    puts@libc.stdio("Can you get the flag?")
    ...

    gets@libc.stdio(buffer)
    ...

    if modified != <X> {
        puts@libc.stdio("Success!")
    } else {
        puts@libc.stdio("Failure!")
    }
}

