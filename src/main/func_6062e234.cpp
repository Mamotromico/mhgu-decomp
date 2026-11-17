extern "C" void func_6056dc28(void *);
extern "C" void func_6062e258(void *);

struct S {
    char pad0[0x50];
    unsigned f50;
    unsigned f54;
};

extern "C" void func_6062e234(S *s)
{
    func_6056dc28(s);
    s->f50 = 0xffffffffu;
    s->f54 = 0xffffffffu;
    func_6062e258(s);
}