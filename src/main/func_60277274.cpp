extern "C" int func_60277274(void *base, int index)
{
    unsigned char *p = (unsigned char *)base + index * 4;
    void *obj = *(void **)(p + 0x1c);
    if (obj == 0)
        return 0;
    int val = *(int *)((unsigned char *)obj + 0x13c8);
    return (val == 1) ? (int)(long)obj : 0;
}