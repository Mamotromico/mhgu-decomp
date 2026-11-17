extern "C" void func_6056e3b0(void *);

struct S {
    char pad0[0x28];
    int field_0x28;
};

struct Inner {
    char pad0[0x6c];
    int (*fn)(void *);
};

extern "C" void func_6064297c(S *self) {
    Inner *inner = *(Inner **)self;
    int r = inner->fn(self);
    self->field_0x28 = r;
    func_6056e3b0(self);
}