extern "C" void func_6019738c(char *r0, unsigned r1, unsigned r2)
{
    if (r1 > 0x16)
        return;
    r0 += r1;
    unsigned char b = (unsigned char)r0[0x6f];
    unsigned v = b + r2;
    if (v >= 0x63)
        v = 0x63;
    r0[0x6f] = (char)v;
}