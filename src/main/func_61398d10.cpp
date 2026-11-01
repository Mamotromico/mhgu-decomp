extern "C" int func_61398d10(const unsigned int *p, int bit)
{
    if (bit > 0x1f)
        return 0;
    return ((*p >> bit) & 1) != 0;
}