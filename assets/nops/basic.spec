block empty {
}

block sleep {
    sleep@libc(<SleepSeconds; random.randint(1, 6)>)
}

