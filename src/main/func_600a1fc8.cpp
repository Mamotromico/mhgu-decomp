extern "C" int func_600a1fc8(void *base, unsigned int mask)
{
    unsigned char *p = *reinterpret_cast<unsigned char **>(
        reinterpret_cast<char *>(base) + 0x1428);
    return (p[0x5e08] & mask) != 0;
}