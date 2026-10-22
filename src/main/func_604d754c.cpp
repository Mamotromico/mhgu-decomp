extern "C" unsigned short func_604d754c(unsigned short **pp)
{
    unsigned short *p = *pp;
    unsigned short v = *p++;
    *pp = p;
    return v;
}