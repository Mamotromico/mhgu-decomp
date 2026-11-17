struct Outer {
    char pad0[4];
    int field4;
};

extern "C" void func_601267a0(Outer *a, void **b)
{
    int (*fn)(void **) = *(int (**)(void **))(*(char **)b + 0xc);
    a->field4 = fn(b);
}