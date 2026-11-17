extern "C" void func_606ccf74(void *);

struct S {
    char pad[4];
    unsigned char b;
};

extern "C" void func_606d40dc(S *s)
{
    func_606ccf74((void *)s);
    s->b = 3;
}