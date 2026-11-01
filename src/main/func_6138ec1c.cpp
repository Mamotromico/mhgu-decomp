extern "C" int func_6138ec1c(const void *p)
{
    const unsigned char *b = (const unsigned char *)p;
    unsigned int v = *(const unsigned int *)(b + 0xac);
    if (v != 5)
        return 0;
    unsigned int w = *(const unsigned int *)(b + 0x98);
    unsigned int d = w - 2;
    return d < 3 ? 1 : 0;
}