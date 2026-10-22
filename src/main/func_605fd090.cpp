extern "C" void func_605fd090(void *context, unsigned char value);

struct Func605fd090State {
    unsigned char pad_0x00[0x60];
    unsigned char flags_0x60;
    unsigned char pad_0x61[0x09];
    unsigned char byte_0x6a;
};

extern "C" void func_605fd090(void *context, unsigned char value) {
    Func605fd090State *state = (Func605fd090State *)context;
    state->byte_0x6a = value;
    state->flags_0x60 = (unsigned char)(state->flags_0x60 | 1);
}