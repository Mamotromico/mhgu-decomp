extern "C" int func_6056e538(void *, int, int);

struct S {
    char pad0[0x50];
    int f50;
    char pad54[0x68 - 0x54];
    void *f68;
};

extern "C" void func_606032fc(void *p)
{
    char *b = (char *)p;
    func_6056e538(p, *(int *)(b + 0x50), *(int *)(*(char **)(b + 0x68) + 0x14));
    *(int *)(b + 0x58) = 2;
}