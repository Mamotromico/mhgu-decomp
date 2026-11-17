extern "C" void func_60e4cbbc(char *p, unsigned char v, float s)
{
    unsigned char *q = *(unsigned char **)(p + 0x1428);
    q[0x5df3] = v;
    unsigned char *r = *(unsigned char **)(p + 0x1428);
    if (r[0x5df3])
        *(float *)(p + 0xcc2c) = s;
}