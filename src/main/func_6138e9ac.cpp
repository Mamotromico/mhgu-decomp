extern "C" int func_6138e9ac(void *p)
{
    char *b = (char *)p;
    if (*(int *)(b + 0xac) != 3)
        return 0;
    unsigned int v = *(unsigned int *)(b + 0x98);
    unsigned int d = v - 2;
    return d < 3 ? 1 : 0;
}