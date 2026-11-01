struct Data_6050d7e8 {
    unsigned char pad[0x471];
    unsigned char field;
};

extern "C" void func_6050d7e8(Data_6050d7e8 *self, unsigned int value)
{
    value = self->field + value;
    if ((unsigned char)value > 10)
        value = 10;
    self->field = (unsigned char)value;
}