extern "C" void func_6054533c(unsigned, unsigned, unsigned);

extern "C" void func_605d3230(unsigned char *p, unsigned a)
{
    unsigned r1 = *(unsigned *)(p + 0x30);
    unsigned r3 = *(unsigned *)(p + 0x24);
    func_6054533c(r3, r1, a);
}