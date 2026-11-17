extern "C" void *func_607af37c(unsigned int size);

struct S {
    char pad[0xac];
    void *field_ac;
};

extern "C" void func_6031d6f8(S *s)
{
    if (s->field_ac == 0)
        s->field_ac = func_607af37c(0x14c);
}