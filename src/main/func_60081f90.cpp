struct Data_60081f90 {
    unsigned char pad[0x1068];
    unsigned char field;
};

extern "C" unsigned int func_60081f90(const Data_60081f90* self) {
    return (self->field >> 6) & 1U;
}