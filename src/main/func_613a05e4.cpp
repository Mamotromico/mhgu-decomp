extern "C" int func_613a05e4(char *p, unsigned short v)
{
    signed cnt = *(signed *)(p + 0x40);
    if (cnt > 0x1f)
        return 0;
    *(unsigned *)(p + 0x40) = cnt + 1;
    *(unsigned short *)(p + cnt * 2) = v;
    return 1;
}