extern "C" int func_603bfec0(unsigned char *p, unsigned int idx);

extern "C" int func_603bfec0(unsigned char *p, unsigned int idx)
{
    if (idx > 3)
        return 0xff;
    if (p[0xaf19] == 1)
        return p[idx + 0xd78a];
    return 0xff;
}