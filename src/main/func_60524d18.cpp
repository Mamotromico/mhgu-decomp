extern "C" unsigned func_60524d18(unsigned char *base, unsigned index)
{
    base += (index >> 5) * 4;
    unsigned value = *(unsigned *)(base + 0x3584);
    return (value & (1u << (index & 0x1f))) != 0;
}