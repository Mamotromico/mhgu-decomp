extern "C" unsigned func_60319188(const unsigned char *p)
{
    unsigned v = *(const unsigned *)(p + 0x68);
    v &= ~1u;
    return v == 0x22 ? 1u : 0u;
}