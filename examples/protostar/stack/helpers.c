#include <stdio.h>
#include <stdlib.h>

void flag() {
    FILE *ff = fopen("flag.txt", "r");
    char buffer[1024];

    while (fread(&buffer, sizeof(char), 1024, ff) != 0) {
        fputs(buffer, stdout);
    }
}

void tryagain() {
    puts("Try again!");
    exit(1);
}

