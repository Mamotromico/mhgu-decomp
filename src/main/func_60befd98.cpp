extern "C" int func_60befd98(void *p, unsigned int bit)
{
    if (bit > 3)
        return 0;
    unsigned int v = *(unsigned int *)((char *)p + 0x31c80);
    return (v & (1u << bit)) != 0;
}