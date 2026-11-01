extern "C" void func_604a2d88(unsigned char *dst, const unsigned char *src)
{
    unsigned char b = src[3];
    unsigned char c = src[5];
    if (c > 0x31u)
        b = c;
    dst[0x159c] = b;
}