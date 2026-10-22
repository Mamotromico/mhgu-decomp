extern "C" unsigned char func_6004ecf8(unsigned int val, unsigned char *a, unsigned char *b, unsigned char *c)
{
    *a = (val >> 12) & 1;
    *b = val;
    return *c = (val >> 8) & 0xF;
}