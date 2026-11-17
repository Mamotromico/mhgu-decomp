extern "C" void func_60285e54(char *base, unsigned bit)
{
    unsigned word = bit >> 5;
    unsigned off = bit & 0x1f;
    unsigned *p = (unsigned *)(base + 0x1424) + word;
    *p |= 1u << off;
}