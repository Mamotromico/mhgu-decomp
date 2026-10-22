struct Func6055f864Data {
    char pad_0000[0x1a4];
    int field_1a4;
    int field_1a8;
};

extern "C" void func_6055f864(Func6055f864Data *self)
{
    int value = 0;
    if (self->field_1a4 == 4)
        value = self->field_1a8;
    self->field_1a4 = value;
}