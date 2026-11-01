extern "C" int func_6052479c(unsigned char *base, unsigned int a, unsigned int b)
{
    unsigned int idx = a + (a << 1);
    base += idx << 5;
    base += (b >> 5) << 2;
    unsigned int bit = b & 0x1f;
    unsigned int word = *(unsigned int *)(base + 0xd98);
    unsigned int v = word & (1u << bit);
    return v != 0 ? 1 : 0;
}