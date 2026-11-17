extern "C" int func_60b85ec4(unsigned char *p, int key)
{
    if (*(unsigned *)(p + 0x44) == 0)
        return 0;
    unsigned count = *(unsigned *)(p + 0x40);
    if (count == 0)
        return 0;
    unsigned char *e = *(unsigned char **)(p + 0x44);
    for (unsigned i = 0; i < count; i++) {
        if (*(int *)(e + 0x4) == key)
            return (int)e;
        e += 0x1c;
    }
    return 0;
}