struct s_600e8390 {
    unsigned char pad[0x2f8];
    unsigned short value;
};

extern "C" void func_600e8390(s_600e8390 *p, unsigned int v)
{
    p->value = v < 0x7530u ? (unsigned short)v : 0x7530u;
}