struct Pair {
    unsigned char pad[6];
    unsigned short six;
    unsigned short eight;
};

extern "C" unsigned short func_600db09c(Pair *p)
{
    unsigned short v = p->eight;
    if (v == 0)
        v = p->six;
    return v;
}