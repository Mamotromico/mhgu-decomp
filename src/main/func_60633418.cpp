extern "C" {
void func_6056dc88(void *);
void func_6054533c(void *, int, int);
}

struct S {
    char pad0[0x24];
    unsigned field_24;
};

extern "C" void func_60633418(S *s) {
    func_6056dc88(s);
    func_6054533c((void *)s->field_24, 0x64, 0);
}