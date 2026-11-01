extern "C" void *func_6027645c(void *base, unsigned int index)
{
    char *result = (char *)base + index * 0x560 + 0x5bdc;
    if (index > 0xbU)
        result = 0;
    return result;
}