extern "C" int func_60153098(char *base, unsigned a1, unsigned a2, unsigned a3)
{
    unsigned count = *(unsigned *)(base + 0x40);
    if (count == 0)
        return 0;
    void **arr = *(void ***)(base + 0x4c);
    for (unsigned i = 0; i < count; i++) {
        char *e = (char *)arr[i];
        char *sub = *(char **)(e + 0x4);
        if (sub == 0)
            continue;
        if (*(unsigned *)(e + 0x8) != a1)
            continue;
        if (*(unsigned *)(e + 0xc) != a2)
            continue;
        if (*(unsigned *)(e + 0x10) != a3)
            continue;
        unsigned char b = *(unsigned char *)(sub + 0x50);
        return (b & 0x11) ? 0 : 1;
    }
    return 0;
}