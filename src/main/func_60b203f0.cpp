struct S {
    char pad0[0xbc];
};

extern "C" void func_60b27600(void *);

extern "C" void func_60b203f0(char *p, int i)
{
    func_60b27600(p + i * 0xbc + 0xd4);
}