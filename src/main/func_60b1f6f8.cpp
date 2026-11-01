extern "C" int func_60b1f6f8(void *a, unsigned int i)
{
    unsigned char *p = (unsigned char *)a;
    unsigned int count = *(unsigned int *)(p + 0x10);
    if (i >= count)
        return 0;
    unsigned char *table = *(unsigned char **)(p + 0x1c);
    void *entry = *(void **)(table + i * 4);
    if (entry == 0)
        return 0;
    return *(int *)((unsigned char *)entry + 0x30);
}