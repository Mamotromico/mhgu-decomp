extern "C" int func_612ace54(unsigned char *dst, unsigned char *src, unsigned char *val);

extern "C" int func_612c3c84(unsigned char *a, unsigned char *b, unsigned char c)
{
    return func_612ace54(a + 0x10, b, &c);
}