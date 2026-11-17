extern "C" void func_60285ea0(unsigned *base, unsigned bit)
{
    base = (unsigned *)((char *)base + (bit >> 5) * 4);
    unsigned *p = (unsigned *)((char *)base + 0x1434);
    *p |= 1u << (bit & 0x1f);
}