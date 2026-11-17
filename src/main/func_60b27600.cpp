extern "C" void func_60b26874(void *, int);

struct S {
    char pad0[0x18];
    int f18;
    int f1c;
    int f20;
    int f24;
    int f28;
};

extern "C" void func_60b27600(struct S *s)
{
    s->f20 = 0;
    s->f24 = -1;
    s->f28 = 0;
    s->f18 = s->f1c;
    func_60b26874(s, 0);
}