struct Inner {
    char pad[0x7c];
    void* field;
};

struct Outer {
    char pad[0x1c0];
    void* field_1c0;
    void* field_1c4;
};

extern "C" void* func_606a64b8(Outer* self, void* value) {
    self->field_1c0 = value;
    Inner* p = static_cast<Inner*>(self->field_1c4);
    if (p) {
        p->field = value;
    }
    return p;
}