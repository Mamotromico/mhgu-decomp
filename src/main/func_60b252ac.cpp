extern "C" int func_60b252ac(char *p, unsigned idx)
{
    if (idx > 3)
        return 0;
    char *q = p + idx * 0x128;
    return (int)((unsigned char)q[0x3030]) != 0;
}