extern "C" void func_60a3682c(char *p, float s0)
{
    float old = *(float *)(p + 0x90);
    if (old == s0)
        return;
    *(float *)(p + 0x90) = s0;
    unsigned v = *(unsigned *)(p + 0x54);
    v |= 0x10000;
    *(unsigned *)(p + 0x54) = v;
}