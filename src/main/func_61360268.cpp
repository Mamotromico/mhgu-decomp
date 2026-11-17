extern char D_61834cd4[];

extern "C" void func_613ef744(void *);

struct S0 {
    void *p;
    char pad[0x44 - 4];
    unsigned z;
};

extern "C" void func_61360268(struct S0 *s)
{
    s->p = (void *)(D_61834cd4 + 8);
    s->z = 0;
    func_613ef744(s);
}