block (nop, func) break {
}

// block (nop) sleep {
//     sleep@libc.unistd(1)
// }
// block (nop) sleep2 {
//     sleep@libc.unistd(2)
// }

block (nop) log {
    puts@libc.stdio("[*] successful")
}
block (nop) log2 {
    puts@libc.stdio("[*] failed")
}
block (nop) log3 {
    puts@libc.stdio("[*] handling expected cases")
}

chunk (static) counter : int = 0
block (nop) log_counter_up {
    counter = counter + 1
    printf@libc.stdio("[*] counter = %d\n", counter)
}
block (nop) log_counter_down {
    counter = counter - 1
    printf@libc.stdio("[*] counter = %d\n", counter)
}

