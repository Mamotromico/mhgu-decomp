extern "C" void func_6122bd9c(void *p, unsigned delta)
{
    char *base = (char *)p;
    unsigned a = *(unsigned *)(base + 0x14);
    unsigned d = *(unsigned *)(base + 0x1c);
    a += delta;
    unsigned q = a / d;
    a -= q * d;
    *(unsigned *)(base + 0x14) = a;
    unsigned b = *(unsigned *)(base + 0x18);
    b -= delta;
    *(unsigned *)(base + 0x18) = b;
}