extern "C" unsigned func_607cc110(unsigned *p)
{
    unsigned a = p[0];
    unsigned b = p[1];
    p[0] = b;
    a = a ^ (a << 15);
    unsigned c = p[2];
    a = a ^ (a >> 4);
    p[1] = c;
    unsigned d = p[3];
    a = a ^ d;
    p[2] = d;
    a = a ^ (d >> 21);
    p[3] = a;
    return a;
}