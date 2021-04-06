#include <stdio.h>
#include <stdlib.h>

void flag() {
    FILE *ff = fopen("flag.txt", "r");
    if (ff == NULL) {
        puts("Couldn't open flag file!");
        return;
    }

    char buffer[1024];
    while (fread(&buffer, sizeof(char), 1024, ff) != 0) {
        fputs(buffer, stdout);
    }
}

void tryagain() {
    puts("Try again!");
    exit(1);
}

