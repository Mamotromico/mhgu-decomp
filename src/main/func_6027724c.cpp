extern "C" int func_6027724c(char *base, int index)
{
    unsigned int *entry = (unsigned int *)(base + index * 4);
    char *obj = *(char **)((char *)entry + 0x1c);
    if (obj == 0)
        return 0;
    unsigned int *p = (unsigned int *)(obj + 0x13c8);
    if (*p != 0)
        return 0;
    return (int)obj;
}