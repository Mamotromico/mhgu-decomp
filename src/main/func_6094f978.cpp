extern "C" {
struct S {
    char pad[0x4a8];
    unsigned int f4a8;
};

S* func_6094f978(S* p, int flag)
{
    unsigned int v = p->f4a8;
    unsigned int r = (v & ~(1u << 26) & 0xFFFFFFFFu) | 0;
    if (flag == 0)
        r = v | 0x4000000u;
    p->f4a8 = r;
    return p;
}
}