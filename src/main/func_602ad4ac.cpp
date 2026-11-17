extern "C" void func_602ad4ac(unsigned *p, unsigned a)
{
    unsigned r1 = (a << 16) & 0x70000u;
    unsigned off = 0x2b70;
    unsigned old = *(unsigned *)((char *)p + off);
    unsigned r3 = old & ~0x3f0000u;
    r1 |= r3;
    r1 |= (old << 3) & 0x380000u;
    *(unsigned *)((char *)p + off) = r1;
}