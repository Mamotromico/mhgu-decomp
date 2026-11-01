extern "C" int func_6018e7f8(const void *p)
{
    unsigned int v = *reinterpret_cast<const unsigned int *>(static_cast<const char *>(p) + 8);
    int result = 0;
    if (v - 0x9c6u < 0x80u)
        result = 1;
    return result;
}