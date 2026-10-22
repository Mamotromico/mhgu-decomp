struct Data_600e9e8c {
    unsigned char pad[0x264];
    unsigned char values[12];
};

extern "C" unsigned char func_600e9e8c(Data_600e9e8c* self, unsigned int index)
{
    return index <= 0xb ? self->values[index] : 0x60;
}