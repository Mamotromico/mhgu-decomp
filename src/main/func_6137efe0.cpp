extern "C" int func_6137efe0(const unsigned char *p)
{
    int ret = 0;
    if (*(const int *)(p + 0xbc) == 3) {
        int v = *(const int *)(p + 0xa8);
        int r1 = v - 2;
        ret = (unsigned)r1 < 3 ? 1 : 0;
    }
    return ret;
}