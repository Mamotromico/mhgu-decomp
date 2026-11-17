extern "C" void *func_6133d280(char *p, unsigned v)
{
    char *q = *(char **)(p + 0x258);
    if (!q)
        return 0;
    if (*(unsigned *)(q + 0x8) == v)
        return q + 0x8;
    if (*(unsigned *)(q + 0x438) == v)
        return q + 0x438;
    if (*(unsigned *)(q + 0x868) == v)
        return q + 0x868;
    if (*(unsigned *)(q + 0xc98) == v)
        return q + 0xc98;
    return 0;
}