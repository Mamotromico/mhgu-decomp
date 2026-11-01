extern "C" int func_606b2154(const unsigned char *base, unsigned int bit)
{
    return (base[0x200 + (bit >> 3)] & (1u << (bit & 7))) != 0;
}