extern "C" void func_6056e4d8(void *);
extern "C" void func_6062f44c(void *, int, int);

struct S {
    char pad[0x4c];
    int field_4c;
};

extern "C" void func_6062f424(S *p)
{
    func_6056e4d8(p);
    if (p->field_4c != 0)
        func_6062f44c(p, p->field_4c, 1);
}