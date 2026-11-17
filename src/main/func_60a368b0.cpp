extern "C" void func_60a368b0(char *p, float value)
{
    float *field = (float *)(p + 0xa0);
    if (*field == value)
        return;
    *field = value;
    *(unsigned *)(p + 0x54) |= 0x10000;
}