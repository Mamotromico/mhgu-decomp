extern "C" int func_60c8d128(void *self, unsigned int index, int flag)
{
    unsigned char *base = (unsigned char *)self;
    unsigned int count = *(unsigned int *)(base + 0x84);
    if (count <= index)
        return 0;
    unsigned char *table = *(unsigned char **)(base + 0x80);
    void *entry = *(void **)(table + index * 16 + 8);
    if (entry == 0)
        return 0;
    if (flag == 1)
        return *(int *)((unsigned char *)entry + 8);
    return (int)(long)entry;
}