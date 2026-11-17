extern "C" void func_608cc64c(char *p, float s0, float s1)
{
    *(float *)(p + 0x38) = s0;
    *(float *)(p + 0x3c) = s1;
    unsigned bits0, bits1;
    __builtin_memcpy(&bits0, &s0, 4);
    __builtin_memcpy(&bits1, &s1, 4);
    unsigned r = bits0 | bits1;
    unsigned ne = r ? 1u : 0u;
    *(unsigned char *)(p + 0x78) = (unsigned char)ne;
}