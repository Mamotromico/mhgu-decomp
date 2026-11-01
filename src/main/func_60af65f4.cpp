extern "C" unsigned int func_60af65f4(const char* p, unsigned int i)
{
    unsigned int count = *(const unsigned int*)(p + 0x18);
    if (count == 0)
        return 0;
    unsigned int limit = *(const unsigned int*)(p + 0x14);
    unsigned int result = 0;
    if (limit > i)
        result = count + (i << 4);
    return result;
}