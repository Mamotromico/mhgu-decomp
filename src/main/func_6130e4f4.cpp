extern "C" int func_6130e4f4(const char *obj, unsigned int idx)
{
    unsigned int v;
    if (idx > 5)
        return 0;
    v = *(const unsigned int *)(obj + 0x5d8);
    v = v & (1u << (idx + 2));
    return v != 0 ? 1 : 0;
}