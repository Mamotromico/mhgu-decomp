extern "C" float func_60282828(void *dst, unsigned len);

extern "C" void func_602a67d4(char *p)
{
    float v = func_60282828(p, 0x54);
    *(float *)(p + 0x2b24) = v;
}