extern "C" int func_606b2134(unsigned char *p, unsigned int bit)
{
    return (p[(bit >> 3) + 0x100] & (1u << (bit & 7))) != 0;
}