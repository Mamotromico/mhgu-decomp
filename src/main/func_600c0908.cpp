extern "C" void func_600c0908(char *p)
{
    if (*(unsigned char *)(p + 0x15e9) & 0x4)
        return;
    void *q = *(void **)(p + 0x1428);
    *(unsigned int *)((char *)q + 0x1c4) = 0x470ca000;
    *(unsigned char *)(p + 0x7429) |= 1;
}