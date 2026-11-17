extern "C" void func_605cf7e0(unsigned char *p, int c)
{
    unsigned v = *(unsigned *)(p + 0x5c);
    unsigned r = v;
    r = (r & ~(1u << 2)) | (0u & (1u << 2));
    if (c != 0)
        r = v | 4;
    *(unsigned *)(p + 0x5c) = r;
}