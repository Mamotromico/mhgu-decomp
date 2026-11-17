extern "C" void func_60966140(unsigned char *p, unsigned char v)
{
    if (*(unsigned char *)(p + 0x40) == v)
        return;
    *(unsigned char *)(p + 0x40) = v;
    *(float *)(p + 0x38) = *(float *)(p + 0x34) + -1.0f;
}