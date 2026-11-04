extern "C" int func_6137a544(char *p)
{
    for (int off = 0x40; off <= 0x138; off += 8)
        *(int *)(p + off) = 0xfd;
    *(int *)(p + 0x140) = 0;
    *(char *)(p + 0x15c) = 0;
    return 1;
}