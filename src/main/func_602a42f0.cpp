extern "C" void func_602a42f0(char *p)
{
    *(unsigned *)(p + 0x2b14) = 0;
    *(unsigned char *)(p + 0x32e9) = 0;
    float *f = (float *)(p + 0x2b18);
    if (*f > 0.0f)
        *(unsigned *)f = 0;
}