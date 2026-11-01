extern "C" void func_61370ffc(char *p)
{
    char *next = *(char **)(p + 4);
    while (next != p) {
        char *n = *(char **)(next + 4);
        *(char **)(next + 0) = 0;
        *(char **)(next + 4) = 0;
        next = n;
    }
    *(char **)(p + 0) = p;
    *(char **)(p + 4) = p;
    *(char **)(p + 8) = 0;
}