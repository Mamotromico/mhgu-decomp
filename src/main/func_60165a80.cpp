extern "C" int func_60165a80(char *p, unsigned idx)
{
    int offset = idx * 0x24; /* (idx + idx*8) * 4 */
    char *base = p + offset;
    if (idx < 0x32)
        return (int)(base + 0x6810);
    return 0;
}