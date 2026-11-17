extern "C" void func_6056e4d8();

struct S {
    char pad[0x4c];
    unsigned char f4c;
};

extern "C" void func_606129a0(S *);

extern "C" void func_6061297c(S *p)
{
    func_6056e4d8();
    if (p->f4c == 0)
        return;
    func_606129a0(p);
}