struct Func600e925cArg {
    unsigned char pad[0x254];
    unsigned char values[16];
};

extern "C" unsigned int func_600e925c(Func600e925cArg *self, unsigned int index) {
    return index <= 0xf ? self->values[index] : 0x39;
}