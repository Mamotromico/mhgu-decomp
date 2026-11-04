extern "C" int func_61390f38(void *p)
{
    unsigned char *b = (unsigned char *)p;
    unsigned int f3c = *(unsigned int *)(b + 0x3c);
    int result = 0;
    if (f3c == 0)
        return 0;
    unsigned int f74 = *(unsigned int *)(b + 0x74);
    unsigned int t = f74 - 2;
    if (t < 3)
        return 0;
    unsigned int f70 = *(unsigned int *)(b + 0x70);
    if (f70 != 3)
        return 0;
    unsigned int u = f70 - 2;
    if (u <= 2)
        result = *(int *)((unsigned char *)f3c + 0x58);
    return result;
}