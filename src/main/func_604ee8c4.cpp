extern "C" int func_604ee8c4(const char *base)
{
    const char *p = base + 0x9fc;
    int result = 1;
    unsigned i = 0;
    do {
        if (p[-0x10] != 0 || p[0] != 0)
            return result;
        i += 2;
        p += 0x20;
    } while (i < 0x40);
    return 0;
}