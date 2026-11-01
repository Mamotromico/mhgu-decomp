extern "C" int func_608c6bc8(void *obj)
{
    unsigned char *p = (unsigned char *)obj;

    if (*(unsigned int *)(p + 0x420) == 0)
        return 0;

    return *(unsigned int *)(p + 0x45c) != 0;
}