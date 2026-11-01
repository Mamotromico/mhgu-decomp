extern "C" int func_60524b04(int a, int b, int c)
{
    unsigned char *base = (unsigned char *)a + b * 0xcc + ((unsigned)c >> 5) * 4;
    unsigned int v = *(unsigned int *)(base + 0x27a8);
    unsigned int mask = 1u << (c & 0x1f);
    return (v & mask) != 0 ? 1 : 0;
}