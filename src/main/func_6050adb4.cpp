extern "C" int func_6050adb4(const char *p)
{
    if (*(const unsigned int *)(p + 0x1e4) == 0x1b)
        return 1;
    return *(const unsigned int *)(p + 0x1e0) == 0x1b ? 1 : 0;
}