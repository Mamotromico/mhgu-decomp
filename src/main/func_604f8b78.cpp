extern "C" void *func_604f8b78(char *self, int a, int b)
{
    unsigned int n = *(unsigned int *)(self + 0x64);
    if (n == 0)
        return 0;
    char *p = *(char **)(self + 0xcc);
    unsigned int i = 0;
    do {
        if ((unsigned char)p[0x20] == a &&
            (unsigned char)p[0x21] == b)
            return p;
        i++;
        p += 0x30;
    } while (i < n);
    return 0;
}