extern "C" void func_60a59268(void *);

struct S {
    char pad[0x46];
    unsigned char f46;
};

extern "C" void func_60a855bc(S *s)
{
    func_60a59268(s);
    s->f46 = 0x34;
}