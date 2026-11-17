extern "C" void func_60285ec4(unsigned base, unsigned bit)
{
    unsigned *p = (unsigned *)(base + 0x1434 + (bit >> 5) * 4);
    *p = *p & ~(1u << (bit & 0x1f));
}