extern "C" int func_60876e94(unsigned char *unused, const unsigned char *p, unsigned int v)
{
    if (v == 0xff)
        return 1;
    if (p[0x50] > v)
        return 0;
    return p[0x51] >= v;
}