struct Inner_605d93e4 {
    char pad0[0x7c];
    void* volatile field_7c;
};

struct Outer_605d93e4 {
    char pad0[0x4c];
    void* volatile field_4c;
    Inner_605d93e4* volatile field_50;
};

extern "C" void func_605d93e4(Outer_605d93e4* self, void* value) {
    self->field_4c = value;
    Inner_605d93e4* inner = self->field_50;
    if (inner != 0) {
        inner->field_7c = value;
    }
}