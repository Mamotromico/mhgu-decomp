extern "C" void func_6056dc28(void *);
extern "C" void func_6062e910(void *, int);

struct S {
    char pad0[0x4c];
    int field_4c;
};

extern "C" void func_6062e8f4(S *self) {
    func_6056dc28(self);
    func_6062e910(self, self->field_4c);
}