extern "C" void func_613940d0(void *arg)
{
    char *base = (char *)arg;
    char *head = base + 0x8;
    char *p = *(char **)(base + 0xc);
    while (p != head) {
        p[0x2d] = 0;
        p = *(char **)(p + 0x4);
    }
}