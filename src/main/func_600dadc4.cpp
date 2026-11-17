extern "C" void *func_607af3a0(unsigned int size);

struct S {
    char pad[0x28];
    void *field_28;
};

extern "C" void func_600dadc4(S *p)
{
    if (p->field_28 == 0)
        p->field_28 = func_607af3a0(0x2c);
}