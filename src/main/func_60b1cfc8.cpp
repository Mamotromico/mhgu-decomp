extern "C" int func_60b1cfc8(const char *obj, unsigned idx)
{
    if (*(const unsigned *)(obj + 0x10) <= idx)
        return 0;
    const char *table = *(const char *const *)(obj + 0x1c);
    const char *entry = *(const char *const *)(table + idx * 4);
    if (entry)
        return *(const int *)(entry + 0x38);
    return 0;
}