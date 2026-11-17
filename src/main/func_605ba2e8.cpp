extern "C" void func_6056e808(unsigned char *p, unsigned int a, unsigned int b, unsigned int c);

struct Buf {
    unsigned char pad[0x54];
    unsigned char f54;
};

extern "C" void func_605ba2e8(Buf *p, unsigned int a, unsigned int b, unsigned int c)
{
    func_6056e808((unsigned char *)p, 1, 1, a);
    p->f54 = (unsigned char)b;
}