extern "C" unsigned func_6136d288(unsigned *p)
{
    unsigned a = p[0];
    unsigned b = p[1];
    p[0] = b;
    a ^= a << 11;
    unsigned c = p[2];
    a ^= a >> 8;
    p[1] = c;
    unsigned d = p[3];
    a ^= d;
    p[2] = d;
    a ^= d >> 19;
    p[3] = a;
    return a;
}