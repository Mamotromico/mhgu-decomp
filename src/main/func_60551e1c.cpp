extern "C" unsigned int func_60551e1c(unsigned int value, unsigned int *high, unsigned int *mask)
{
    *high = value >> 5;
    return *mask = 1u << (value & 0x1f);
}