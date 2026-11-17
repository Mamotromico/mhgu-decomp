extern "C" void func_6060294c(void);

struct S {
    char pad[0x58];
    unsigned field_0x58;
};

extern "C" void func_6057a548(S *s) {
    func_6060294c();
    s->field_0x58 = 2;
}