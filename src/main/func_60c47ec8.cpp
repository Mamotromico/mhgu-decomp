extern "C" unsigned func_60c47ec8(char *a, int i)
{
    unsigned r = 0;
    if (i != -1 && *(unsigned *)(a + 0xbc) > (unsigned)i) {
        unsigned *p = *(unsigned **)(a + 0xc8);
        unsigned v = p[i];
        if (v != 0)
            r = *(unsigned char *)(v + 0x18);
    }
    return r;
}