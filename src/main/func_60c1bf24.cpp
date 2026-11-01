extern "C" int func_60c1bf24(const unsigned char *obj)
{
    int result = 0;
    if (obj[0x32] != 0) {
        const unsigned char *p = *(const unsigned char *const *)(obj + 0x2c);
        if (p != 0) {
            unsigned int v = *(const unsigned int *)(p + 0xc);
            result = ((v & 7u) < 3u) ? 1 : 0;
        }
    }
    return result;
}