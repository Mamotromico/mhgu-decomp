extern "C" int func_601fed90(void *, void *);

struct S0_602039f4 {
    char pad[0x98];
    float f98;
};

struct S1_602039f4 {
    char pad[0x464];
    float (*fn)(void *);
};

extern "C" void func_602039f4(void *a, void *b)
{
    func_601fed90(a, b);
    S1_602039f4 *p = *(S1_602039f4 **)b;
    float r = p->fn(b);
    ((S0_602039f4 *)a)->f98 = r;
}