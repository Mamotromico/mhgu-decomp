extern "C" void func_6055f208(char *p, int a, int b, float s0, float s1, const char *r3)
{
    p[0x20] = 1;
    *(int *)(p + 0x24) = a;
    *(int *)(p + 0x28) = b;
    *(int *)(p + 0x30) = *(const int *)(r3 + 0);
    *(int *)(p + 0x34) = *(const int *)(r3 + 4);
    *(float *)(p + 0x38) = s0;
    *(float *)(p + 0x3c) = s1;
    p[0x200] = 1;
}