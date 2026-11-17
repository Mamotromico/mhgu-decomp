extern "C" void func_601ff308(void *, void *);

struct S5 {
    char pad0[0x98];
    unsigned short f98;
};

extern "C" void func_602053b0(S5 *a, char *b)
{
    func_601ff308(a, b);
    unsigned short v = a->f98;
    *(unsigned short *)(b + 0x3266) = v;
}