extern "C" int func_603a314c(unsigned char *p)
{
    unsigned int v = *(unsigned int *)(p + 0xa4);
    if (v == 0)
        return 0;
    unsigned char b = *(unsigned char *)(v + 0x10);
    unsigned int r = (unsigned char)(b + 0x63);
    return r > 0xc6 ? 1 : 0;
}