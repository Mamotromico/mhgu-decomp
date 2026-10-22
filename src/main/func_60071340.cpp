struct Inner_60071340 {
    char pad_0000[0x94];
    void* field_0094;
    char pad_0098[0xc8 - 0x98];
    unsigned char field_00c8;
};

struct Outer_60071340 {
    char pad_0000[0x75e8];
    Inner_60071340* field_75e8;
};

extern "C" void* func_60071340(Outer_60071340* self) {
    Inner_60071340* inner = self->field_75e8;
    return inner->field_00c8 != 0 ? inner->field_0094 : 0;
}