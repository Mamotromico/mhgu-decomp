extern "C" unsigned func_611e22d8(char *p)
{
    unsigned char v = *(unsigned char *)(p + 0x334f);
    unsigned char r = (unsigned char)(v + 1);
    if (v > 7)
        r = 8;
    *(unsigned char *)(p + 0x334f) = r;
    return v < 8 ? 1 : 0;
}